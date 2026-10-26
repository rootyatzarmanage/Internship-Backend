import logging
import uuid
from datetime import datetime, timedelta, timezone

import razorpay
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.config import get_settings
from ycpa.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from ycpa.models.subscription import AimSubscription, PimSubscription, SubscriptionPlan
from ycpa.models.user import User
from ycpa.services.base import BaseService

logger = logging.getLogger(__name__)
settings = get_settings()


PLAN_PRICES = {
    ("pim", "professional", "monthly"):   299900,
    ("pim", "professional", "yearly"):   2999000,
    ("pim", "enterprise",   "monthly"):   799900,
    ("pim", "enterprise",   "yearly"):   7999000,
    ("aim", "professional", "monthly"):   249900,
    ("aim", "professional", "yearly"):   2499000,
    ("aim", "enterprise",   "monthly"):   599900,
    ("aim", "enterprise",   "yearly"):   5999000,
}


class BillingService(BaseService):

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self._rzp = razorpay.Client(
            auth=(
                settings.RAZORPAY_KEY_ID,
                settings.RAZORPAY_KEY_SECRET.get_secret_value(),
            )
        )


    async def create_order(
        self,
        user: User,
        product_type: str,
        plan: str,
        billing_period: str,
    ) -> dict:
        amount = PLAN_PRICES.get((product_type, plan, billing_period))
        if not amount:
            raise BadRequestException(
                f"Invalid plan: {product_type}/{plan}/{billing_period}"
            )

        try:
            order = self._rzp.order.create({
                "amount":   amount,
                "currency": "INR",
                "receipt": f"ord_{str(user.id).replace('-', '')[:20]}",

                "notes": {
                    "user_id":        str(user.id),
                    "product_type":   product_type,
                    "plan":           plan,
                    "billing_period": billing_period,
                },
            })
        except Exception as e:
            logger.error(
                "Razorpay order creation failed",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise BadRequestException(
                "Failed to create payment order. Please try again."
            )

        logger.info(
            "Razorpay order created",
            extra={
                "user_id":  str(user.id),
                "order_id": order["id"],
                "amount":   amount,
            },
        )

        from ycpa.models.order import Order as OrderModel

        db_order = OrderModel(
            user_id=user.id,
            razorpay_order_id=order["id"],
            amount=amount,
            currency="INR",
            status="created",
            product_type=product_type,
            plan=plan,
            billing_period=billing_period,
        )
        self.session.add(db_order)
        await self.session.commit()

        return {
            "order_id":       order["id"],
            "amount":         amount,
            "currency":       "INR",
            "key_id":         settings.RAZORPAY_KEY_ID,
            "plan":           plan,
            "product_type":   product_type,
            "billing_period": billing_period,
        }


    async def upgrade_subscription(
        self,
        user: User,
        razorpay_payment_id: str,
        razorpay_order_id: str,
    ) -> dict:
        # ── Resolve what was actually paid for from Razorpay — never from the client ──
        # The client only supplies opaque ids; the plan, amount and ownership are read
        # back from the server-created order so a caller cannot claim a higher plan
        # than they paid for.
        try:
            order   = self._rzp.order.fetch(razorpay_order_id)
            payment = self._rzp.payment.fetch(razorpay_payment_id)
        except Exception as e:
            logger.error(
                "Razorpay fetch failed during verification",
                extra={"error": str(e), "order_id": razorpay_order_id},
                exc_info=True,
            )
            raise BadRequestException("Could not verify the payment with Razorpay.")

        if payment.get("order_id") != razorpay_order_id:
            raise BadRequestException("Payment does not belong to this order.")
        if payment.get("status") != "captured":
            raise BadRequestException("Payment has not been captured.")
        if payment.get("amount") != order.get("amount"):
            raise BadRequestException("Paid amount does not match the order amount.")

        notes = order.get("notes") or {}
        if notes.get("user_id") != str(user.id):
            raise ForbiddenException("This order does not belong to you.")

        product_type   = notes.get("product_type")
        plan           = notes.get("plan")
        billing_period = notes.get("billing_period")

        expected_amount = PLAN_PRICES.get((product_type, plan, billing_period))
        if expected_amount is None or expected_amount != order.get("amount"):
            raise BadRequestException("Order amount does not match the plan price.")

        # Idempotency — a captured payment may upgrade exactly one subscription once.
        for sub_model in (PimSubscription, AimSubscription):
            seen = await self.session.scalar(
                select(sub_model).where(sub_model.stripe_price_id == razorpay_payment_id)
            )
            if seen:
                raise BadRequestException("This payment has already been processed.")

        # Fetch plan config from subscription_plans table
        plan_config = await self.session.scalar(
            select(SubscriptionPlan).where(
                SubscriptionPlan.product_type == product_type,
                SubscriptionPlan.name == plan,
                SubscriptionPlan.is_active.is_(True),
            )
        )
        if not plan_config:
            raise NotFoundException(
                f"Subscription plan '{plan}' not found for {product_type}"
            )

        now = datetime.now(timezone.utc)
        period_end = now + timedelta(days=30 if billing_period == "monthly" else 365)

        if product_type == "pim":
            sub = await self.session.scalar(
                select(PimSubscription).where(PimSubscription.user_id == user.id)
            )
            if not sub:
                raise NotFoundException("PIM subscription not found")

            old_plan = sub.plan

            sub.plan                           = plan
            sub.status                         = "active"
            sub.max_pim_workspaces             = plan_config.max_workspaces
            sub.max_projects_per_pim_workspace = plan_config.max_projects_per_workspace
            sub.max_members_per_workspace      = plan_config.max_members_per_workspace
            sub.max_members_per_project        = plan_config.max_members_per_workspace
            sub.can_use_4d                     = plan_config.can_use_4d
            sub.can_use_5d                     = plan_config.can_use_5d
            sub.can_use_clash_detection        = plan_config.can_use_clash_detection
            sub.can_export_bcf                 = plan_config.can_export_bcf
            sub.can_use_api                    = plan_config.can_use_api
            sub.billing_period                 = billing_period
            sub.current_period_start           = now
            sub.current_period_end             = period_end
            sub.stripe_subscription_id         = razorpay_order_id
            sub.stripe_price_id                = razorpay_payment_id

        else:
            sub = await self.session.scalar(
                select(AimSubscription).where(AimSubscription.user_id == user.id)
            )
            if not sub:
                raise NotFoundException("AIM subscription not found")

            old_plan = sub.plan

            sub.plan                           = plan
            sub.status                         = "active"
            sub.max_aim_workspaces             = plan_config.max_workspaces
            sub.max_projects_per_aim_workspace = plan_config.max_projects_per_workspace
            sub.max_members_per_workspace      = plan_config.max_members_per_workspace
            sub.max_members_per_project        = plan_config.max_members_per_workspace
            sub.can_use_ai                     = plan_config.can_use_ai
            sub.can_use_maintenance            = plan_config.can_use_maintenance
            sub.can_use_facility               = plan_config.can_use_facility
            sub.can_use_api                    = plan_config.can_use_api
            sub.billing_period                 = billing_period
            sub.current_period_start           = now
            sub.current_period_end             = period_end
            sub.stripe_subscription_id         = razorpay_order_id
            sub.stripe_price_id                = razorpay_payment_id

        await self.log_audit(
            action="SUBSCRIPTION_UPGRADED",
            resource_type=f"{product_type}_subscription",
            resource_id=str(sub.id),
            user_id=user.id,
            changed_from={"plan": old_plan},
            changed_to={"plan": plan, "billing_period": billing_period},
            payload={
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_order_id":   razorpay_order_id,
            },
        )

        from ycpa.models.order import Order as OrderModel
        db_order = await self.session.scalar(
            select(OrderModel).where(OrderModel.razorpay_order_id == razorpay_order_id)
        )
        if db_order:
            db_order.status = "paid"
            db_order.razorpay_payment_id = razorpay_payment_id
            db_order.transaction_id = payment.get("acq_data", {}).get("txn_id") or razorpay_payment_id
            db_order.payment_method = payment.get("method")

        await self.session.commit()

        logger.info(
            "Subscription upgraded",
            extra={
                "user_id":      str(user.id),
                "product_type": product_type,
                "old_plan":     old_plan,
                "new_plan":     plan,
                "billing":      billing_period,
            },
        )

        return {
            "plan":                       plan,
            "product_type":               product_type,
            "billing_period":             billing_period,
            "max_workspaces":             plan_config.max_workspaces,
            "max_projects_per_workspace": plan_config.max_projects_per_workspace,
            "max_members_per_workspace":  plan_config.max_members_per_workspace,
            "max_storage_bytes":          plan_config.max_storage_bytes,
            "can_use_4d":                 plan_config.can_use_4d,
            "can_use_5d":                 plan_config.can_use_5d,
            "can_use_clash_detection":    plan_config.can_use_clash_detection,
            "can_use_ai":                 plan_config.can_use_ai,
            "can_use_facility":           plan_config.can_use_facility,
            "can_use_api":                plan_config.can_use_api,
        }