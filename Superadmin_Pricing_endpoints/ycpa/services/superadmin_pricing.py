import logging
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.config import get_settings
from ycpa.core.exceptions import BadRequestException, ExternalServiceException, NotFoundException
from ycpa.models.superadmin_pricing import SuperadminPricing
from ycpa.models.user import User
from ycpa.repositories.superadmin_pricing import PRICING_SLUG, SuperadminPricingRepository
from ycpa.schemas.requests.superadmin_pricing import SaveSuperadminPricingRequest
from ycpa.services.base import BaseService

logger = logging.getLogger(__name__)

class SuperadminPricingService(BaseService):

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.repo = SuperadminPricingRepository(session)

    async def get_pricing(self) -> SuperadminPricing | None:
        return await self.repo.get_pricing()

    async def save_pricing(self, body: SaveSuperadminPricingRequest, user: User) -> SuperadminPricing:
        values = self._to_values(body)
        row = await self.repo.get_pricing()

        if row is None:
            row = await self.repo.create(
                SuperadminPricing(slug=PRICING_SLUG, created_by=user.id, updated_by=user.id, **values)
            )
            await self.log_audit("create", "superadmin_pricing", row.id, user.id, changed_to=values)
            return row

        before = self._to_values_from_row(row)
        row = await self.repo.update_by_id(row.id, {**values, "updated_by": user.id})
        await self.log_audit(
            "update", "superadmin_pricing", row.id, user.id, changed_from=before, changed_to=values
        )
        return row

    async def convert_pricing(self, to: str) -> dict:
        row = await self.repo.get_pricing()
        if row is None:
            raise NotFoundException("Pricing is not configured yet.")

        base, target = row.currency_code.upper(), to.upper()
        rate, rate_date = (Decimal(1), None) if base == target else await self._fetch_rate(base, target)

        plans = [
            {
                **plan,
                "prices": {
                    tab_id: {"p": self._convert_amount(price["p"], rate), "n": price["n"]}
                    for tab_id, price in plan["prices"].items()
                },
            }
            for plan in row.plans
        ]
        return {
            "base_currency_code": base,
            "currency_code": target,
            "rate": float(rate),
            "rate_date": rate_date,
            "plans": plans,
        }

    @staticmethod
    async def _fetch_rate(base: str, target: str) -> tuple[Decimal, str | None]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(str(get_settings().FRANKFURTER_URL), params={"base": base, "symbols": target})
            if resp.status_code in (404, 422):
                raise BadRequestException(f"Unsupported currency: {base} -> {target}")
            resp.raise_for_status()
            data = resp.json()
            return Decimal(str(data["rates"][target])), data.get("date")
        except BadRequestException:
            raise
        except (httpx.HTTPError, KeyError, ValueError, InvalidOperation) as e:
            logger.error("Frankfurter request failed", extra={"base": base, "target": target, "error": str(e)}, exc_info=True)
            raise ExternalServiceException("Currency conversion service is unavailable.", service_name="frankfurter")

    @staticmethod
    def _convert_amount(text: str, rate: Decimal) -> str:
        try:
            value = Decimal(text.replace(",", "").strip())
        except InvalidOperation:
            return text
        if not value.is_finite():
            return text
        converted = (value * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return f"{converted:,.2f}".removesuffix(".00")

    @staticmethod
    def _to_values(body: SaveSuperadminPricingRequest) -> dict:
        data = body.model_dump()
        tab_ids = [t["id"] for t in data["tabs"]]
        feature_ids = {f["id"] for f in data["features"]}

        for plan in data["plans"]:
            plan["prices"] = {t: plan["prices"].get(t, {"p": "", "n": ""}) for t in tab_ids}
            plan["feat"] = {f: True for f, on in plan["feat"].items() if on and f in feature_ids}

        return {
            "currency": data["cur"],
            "currency_code": data["cur_code"],
            "active_tab_id": data["active"],
            "theme": data["theme"],
            "tabs": data["tabs"],
            "features": data["features"],
            "plans": data["plans"],
        }

    @staticmethod
    def _to_values_from_row(row: SuperadminPricing) -> dict:
        return {
            "currency": row.currency,
            "currency_code": row.currency_code,
            "active_tab_id": row.active_tab_id,
            "theme": row.theme,
            "tabs": row.tabs,
            "features": row.features,
            "plans": row.plans,
        }
