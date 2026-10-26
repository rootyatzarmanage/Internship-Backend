"""
Subscription Plans Seeder
=========================

Run with:
    uv run python -m ycpa.seeders.seed_subscription_plans

What this seeds:
  - 3 PIM plans: starter, professional, enterprise
  - 3 AIM plans: starter, professional, enterprise

Pricing in INR paise (₹1 = 100 paise)
  PIM Professional  → ₹2,999/mo  | ₹29,990/yr  (~2 months free)
  PIM Enterprise    → ₹7,999/mo  | ₹79,990/yr  (~2 months free)
  AIM Professional  → ₹2,499/mo  | ₹24,990/yr  (~2 months free)
  AIM Enterprise    → ₹5,999/mo  | ₹59,990/yr  (~2 months free)

Safe to run multiple times — updates prices if plan already exists,
skips limits/flags so manual overrides are preserved.
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.database.session import AsyncSessionLocal
from ycpa.models.subscription import SubscriptionPlan

PLANS = [
    # ── PIM ──────────────────────────────────────────────────────────────────

    {
        "product_type": "pim",
        "name": "starter",
        "display_name": "PIM Starter",
        "description": "Get started with BIM project management. Free forever.",
        "price_monthly": 0,
        "price_yearly":  0,
        "order": 1,
        "is_default": True,
        "is_active": True,
        "max_workspaces": 1,
        "max_projects_per_workspace": 1,
        "max_members_per_workspace": 5,
        "max_members_per_project": 5,
        "max_storage_bytes": 2_147_483_648,
        "can_use_4d": False,
        "can_use_5d": False,
        "can_use_clash_detection": False,
        "can_export_bcf": True,
        "can_use_ai": False,
        "can_use_maintenance": False,
        "can_use_facility": False,
        "can_use_api": False,
    },

    {
        "product_type": "pim",
        "name": "professional",
        "display_name": "PIM Professional",
        "description": "For growing BIM teams — 4D scheduling, more workspaces and storage.",
        "price_monthly": 299900,
        "price_yearly":  2999000,
        "order": 2,
        "is_default": False,
        "is_active": True,
        "max_workspaces": 5,
        "max_projects_per_workspace": 10,
        "max_members_per_workspace": 25,
        "max_members_per_project": 25,
        "max_storage_bytes": 53_687_091_200,  # 50 GB
        "can_use_4d": True,
        "can_use_5d": False,
        "can_use_clash_detection": False,
        "can_export_bcf": True,
        "can_use_ai": False,
        "can_use_maintenance": False,
        "can_use_facility": False,
        "can_use_api": False,
    },

    {
        "product_type": "pim",
        "name": "enterprise",
        "display_name": "PIM Enterprise",
        "description": "Full BIM suite — 4D, 5D, clash detection, unlimited scale and API access.",
        "price_monthly": 799900,
        "price_yearly":  7999000,
        "order": 3,
        "is_default": False,
        "is_active": True,
        "max_workspaces": -1,
        "max_projects_per_workspace": -1,
        "max_members_per_workspace": -1,
        "max_members_per_project": -1,
        "max_storage_bytes": -1,
        "can_use_4d": True,
        "can_use_5d": True,
        "can_use_clash_detection": True,
        "can_export_bcf": True,
        "can_use_ai": False,
        "can_use_maintenance": False,
        "can_use_facility": False,
        "can_use_api": True,
    },

    # ── AIM ──────────────────────────────────────────────────────────────────

    {
        "product_type": "aim",
        "name": "starter",
        "display_name": "AIM Starter",
        "description": "Get started with asset and maintenance management. Free forever.",
        "price_monthly": 0,
        "price_yearly":  0,
        "order": 1,
        "is_default": True,
        "is_active": True,
        "max_workspaces": 1,
        "max_projects_per_workspace": 1,
        "max_members_per_workspace": 5,
        "max_members_per_project": 5,
        "max_storage_bytes": 2_147_483_648,
        "can_use_4d": False,
        "can_use_5d": False,
        "can_use_clash_detection": False,
        "can_export_bcf": True,
        "can_use_ai": False,
        "can_use_maintenance": True,
        "can_use_facility": False,
        "can_use_api": False,
    },

    {
        "product_type": "aim",
        "name": "professional",
        "display_name": "AIM Professional",
        "description": "For facility teams — full maintenance and facility management modules.",
        "price_monthly": 249900,
        "price_yearly":  2499000,
        "order": 2,
        "is_default": False,
        "is_active": True,
        "max_workspaces": 5,
        "max_projects_per_workspace": 10,
        "max_members_per_workspace": 25,
        "max_members_per_project": 25,
        "max_storage_bytes": 53_687_091_200,
        "can_use_4d": False,
        "can_use_5d": False,
        "can_use_clash_detection": False,
        "can_export_bcf": True,
        "can_use_ai": False,
        "can_use_maintenance": True,
        "can_use_facility": True,
        "can_use_api": False,
    },

    {
        "product_type": "aim",
        "name": "enterprise",
        "display_name": "AIM Enterprise",
        "description": "Unlimited asset management with AI insights and full API access.",
        "price_monthly": 599900,
        "price_yearly":  5999000,
        "order": 3,
        "is_default": False,
        "is_active": True,
        "max_workspaces": -1,
        "max_projects_per_workspace": -1,
        "max_members_per_workspace": -1,
        "max_members_per_project": -1,
        "max_storage_bytes": -1,
        "can_use_4d": False,
        "can_use_5d": False,
        "can_use_clash_detection": False,
        "can_export_bcf": True,
        "can_use_ai": True,
        "can_use_maintenance": True,
        "can_use_facility": True,
        "can_use_api": True,
    },
]



async def seed_plans(session: AsyncSession) -> None:
    print("\n Seeding subscription plans")

    for plan_data in PLANS:
        result = await session.execute(
            select(SubscriptionPlan).where(
                SubscriptionPlan.product_type == plan_data["product_type"],
                SubscriptionPlan.name == plan_data["name"],
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.price_monthly = plan_data["price_monthly"]
            existing.price_yearly  = plan_data["price_yearly"]
            existing.display_name  = plan_data["display_name"]
            existing.description   = plan_data["description"]
            print(f"  UPDATE  {plan_data['product_type'].upper()} › {plan_data['name']}")
        else:
            plan = SubscriptionPlan(**plan_data)
            session.add(plan)
            print(f"    {plan_data['product_type'].upper()} › {plan_data['name']}")



async def main():
    print("=" * 50)
    print("  Subscription Plans Seeder starting...")
    print("=" * 50)

    async with AsyncSessionLocal() as session:
        async with session.begin():
            await seed_plans(session)

    print("\n" + "=" * 50)
    print("  Subscription Plans Seeder complete")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
