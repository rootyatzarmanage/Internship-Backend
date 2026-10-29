"""
RBAC Seeder  (v2)
=================

Run with:
    uv run python -m ycpa.seeders.seed_rbac

What this seeds:
  1. Roles         → 13 real construction roles  (product_type = both/pim/aim)
  2. Modules       → 12 modules
  3. Submodules    → CDE submodules (WIP, Shared, Published, Archived)
  4. Permissions   → full matrix per role × module (+ submodule for CDE)

Role groups
  MANAGEMENT    BIM Manager, Project Manager
  ENGINEERING   Structural Engineer, MEP Engineer, Architect, Civil Engineer
  COST/PLAN     Cost Consultant, Planning Engineer
  CLIENT        Client Representative, Client Viewer
  SITE          Site Engineer, Site Supervisor
  FACILITY      Facility Manager  (AIM)

All roles are:
  is_system   = True
  is_editable = True   ← super_admin AND workspace owner can tweak permissions
  workspace_id = NULL  ← platform-wide, available to all workspaces

Safe to re-run — skips existing rows.
"""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ycpa.core.database.session import AsyncSessionLocal
from ycpa.models.rbac import Module, RolePermission, Submodule
from ycpa.models.roles import Role



ROLES_TO_SEED = [

    {
        "name":        "Owner",
        "description": "workspace:owner — Full control, cannot be removed",
        "product_type": "both",
        "is_system":   True,
        "is_editable": False,
    },
    {
        "name":        "Admin",
        "description": "workspace:admin — Manage team and projects",
        "product_type": "both",
        "is_system":   True,
        "is_editable": False,
    },
    {
        "name":        "Member",
        "description": "workspace:member — View workspace, access assigned projects",
        "product_type": "both",
        "is_system":   True,
        "is_editable": False,
    },

    {
        "name":        "BIM Manager",
        "description": "Full access to all modules. Responsible for overall BIM execution.",
        "product_type": "both",
        "is_system":   True,
        "is_editable": True,
    },
    {
        "name":        "Project Manager",
        "description": "Full project oversight. Access to team, scope, cost, summary. Limited technical modules.",
        "product_type": "both",
        "is_system":   True,
        "is_editable": True,
    },

    {
        "name":        "Structural Engineer",
        "description": "CDE full access, IFC Viewer, BCF, Clash Detection. No cost or team management.",
        "product_type": "pim",
        "is_system":   True,
        "is_editable": True,
    },
    {
        "name":        "MEP Engineer",
        "description": "Mechanical, Electrical & Plumbing. CDE, IFC Viewer, BCF, Clash Detection.",
        "product_type": "pim",
        "is_system":   True,
        "is_editable": True,
    },
    {
        "name":        "Architect",
        "description": "CDE full access, IFC Viewer, BCF, Scope. Design lead role.",
        "product_type": "pim",
        "is_system":   True,
        "is_editable": True,
    },
    {
        "name":        "Civil Engineer",
        "description": "CDE, IFC Viewer, BCF access. Site and infrastructure focused.",
        "product_type": "pim",
        "is_system":   True,
        "is_editable": True,
    },

    {
        "name":        "Cost Consultant",
        "description": "Full Cost module access. CDE view only. Also known as QS / Quantity Surveyor.",
        "product_type": "pim",
        "is_system":   True,
        "is_editable": True,
    },
    {
        "name":        "Planning Engineer",
        "description": "4D full access, 5D view. CDE view. Schedule and timeline management.",
        "product_type": "pim",
        "is_system":   True,
        "is_editable": True,
    },

    {
        "name":        "Client Representative",
        "description": "Summary, CDE published docs, IFC view. Approval rights. No editing.",
        "product_type": "both",
        "is_system":   True,
        "is_editable": True,
    },
    {
        "name":        "Client Viewer",
        "description": "Read-only access. Summary and published CDE documents only.",
        "product_type": "both",
        "is_system":   True,
        "is_editable": True,
    },

    {
        "name":        "Site Engineer",
        "description": "CDE, BCF, IFC Viewer access. On-site execution team.",
        "product_type": "pim",
        "is_system":   True,
        "is_editable": True,
    },
    {
        "name":        "Site Supervisor",
        "description": "View-only on CDE, BCF, IFC. Monitor site activities.",
        "product_type": "pim",
        "is_system":   True,
        "is_editable": True,
    },

    {
        "name":        "Facility Manager",
        "description": "Full AIM access. Manages building operations post-handover.",
        "product_type": "aim",
        "is_system":   True,
        "is_editable": True,
    },
    {
        "name":        "Maintenance Engineer",
        "description": "Maintenance and Facility modules. CDE view for as-built docs.",
        "product_type": "aim",
        "is_system":   True,
        "is_editable": True,
    },
]



MODULES_TO_SEED = [
    {"name": "Overview",         "slug": "overview",         "product_type": "both", "order": 1},
    {"name": "Team",            "slug": "team",            "product_type": "both", "order": 2},
    {"name": "Documents",             "slug": "documents",             "product_type": "both", "order": 3},
    {"name": "Scope",      "slug": "scope",      "product_type": "both", "order": 4},
    {"name": "Model",             "slug": "model",             "product_type": "both", "order": 5},
    {"name": "Meetings",           "slug": "meetings",           "product_type": "pim",  "order": 6},
    {"name": "Quantities",            "slug": "quantities",            "product_type": "pim",  "order": 7},
    {"name": "Estimate",              "slug": "estimate",              "product_type": "pim",  "order": 8},
    {"name": "Programme",              "slug": "programme",              "product_type": "pim",  "order": 9},
    {"name": "Menu",            "slug": "menu",            "product_type": "pim",  "order": 15},
]



CDE_SUBMODULES_TO_SEED = [
    {"name": "WIP",       "slug": "wip",       "order": 1},
    {"name": "Shared",    "slug": "shared",    "order": 2},
    {"name": "Published", "slug": "published", "order": 3},
    {"name": "Archived",  "slug": "archived",  "order": 4},
]

MENU_SUBMODULES_TO_SEED = [
    {"name": "IDS Maker",      "slug": "ids_maker",      "order": 1},
    {"name": "Vendor",         "slug": "vendor",         "order": 2},
    {"name": "Equipment",      "slug": "equipment",      "order": 3},
    {"name": "Material",       "slug": "material",       "order": 4},
    {"name": "Human Resource", "slug": "human_resource", "order": 5},
]



def p(view=False, create=False, edit=False, delete=False, approve=False, share=False):
    return {
        "can_view": view, "can_create": create, "can_edit": edit,
        "can_delete": delete, "can_approve": approve, "can_share": share,
    }

FULL = p(True, True, True, True, True, True)
VIEW = p(view=True)
NONE = p()
APPROVE_ONLY = p(view=True, approve=True)


MODULE_PERMISSIONS: dict[str, dict[str, dict]] = {


    "BIM Manager": {
        "overview":         FULL,
        "team":            FULL,
        "documents":             FULL,
        "scope":      FULL,
        "model":             FULL,
        "meetings":           FULL,
        "quantities":            FULL,
        "estimate":              FULL,
        "programme":              FULL,
        "menu": FULL,
    },

    "Project Manager": {
        "overview":         FULL,
        "team":            FULL,
        "documents":             p(True, True, True, False, True, True),
        "scope":      VIEW,
        "model":             p(True, False, False, False, True, False),
        "meetings":           FULL,
        "quantities":            FULL,
        "estimate":              FULL,
        "programme":              FULL,
        "menu": VIEW,
    },


    "Structural Engineer": {
        "overview":         VIEW,
        "team":            NONE,
        "documents":             p(True, True, True, False, True, True),
        "scope":      p(True, True, True, False, False, True),
        "model":             p(True, True, True, False, True, True),
        "meetings":           VIEW,
        "quantities":            NONE,
        "estimate":              VIEW,
        "programme":              NONE,
        "menu": p(True, True, True, False, True, True),
    },

    "MEP Engineer": {
        "overview":         VIEW,
        "team":            NONE,
        "documents":             p(True, True, True, False, True, True),
        "scope":      p(True, True, True, False, False, True),
        "model":             p(True, True, True, False, True, True),
        "meetings":           VIEW,
        "quantities":            NONE,
        "estimate":              VIEW,
        "programme":              NONE,
        "menu": p(True, True, True, False, True, True),
    },

    "Architect": {
        "overview":         VIEW,
        "team":            NONE,
        "documents":             p(True, True, True, False, True, True),
        "scope":      p(True, True, True, False, False, True),
        "model":             p(True, True, True, False, True, True),
        "meetings":           p(True, True, True, False, True, False),
        "quantities":            NONE,
        "estimate":              VIEW,
        "programme":              NONE,
        "menu": VIEW,
    },

    "Civil Engineer": {
        "overview":         VIEW,
        "team":            NONE,
        "documents":             p(True, True, True, False, True, True),
        "scope":      p(True, True, True, False, False, True),
        "model":             p(True, True, True, False, True, True),
        "meetings":           VIEW,
        "quantities":            NONE,
        "estimate":              VIEW,
        "programme":              NONE,
        "menu": VIEW,
    },


    "Cost Consultant": {
        "overview":         VIEW,
        "team":            NONE,
        "documents":             VIEW,
        "scope":      VIEW,
        "model":             NONE,
        "meetings":           VIEW,
        "quantities":            FULL,
        "estimate":              VIEW,
        "programme":              FULL,
        "menu": NONE,
    },

    "Planning Engineer": {
        "overview":         VIEW,
        "team":            NONE,
        "documents":             VIEW,
        "scope":      VIEW,
        "model":             NONE,
        "meetings":           VIEW,
        "quantities":            VIEW,
        "estimate":              FULL,
        "programme":              VIEW,
        "menu": NONE,
    },


    "Client Representative": {
        "overview":         p(True, False, False, False, True, False),
        "team":            NONE,
        "documents":             p(True, False, False, False, True, False),  # published only via submodule
        "scope":      VIEW,
        "model":             NONE,
        "meetings":           VIEW,
        "quantities":            VIEW,
        "estimate":              VIEW,
        "programme":              VIEW,
        "menu": NONE,
    },

    "Client Viewer": {
        "overview":         VIEW,
        "team":            NONE,
        "documents":             VIEW,
        "scope":      VIEW,
        "model":             NONE,
        "meetings":           NONE,
        "quantities":            NONE,
        "estimate":              NONE,
        "programme":              NONE,
        "menu": NONE,
    },


    "Site Engineer": {
        "overview":         VIEW,
        "team":            NONE,
        "documents":             p(True, True, True, False, False, False),
        "scope":      VIEW,
        "model":             p(True, True, True, False, False, False),
        "meetings":           VIEW,
        "quantities":            NONE,
        "estimate":              VIEW,
        "programme":              NONE,
        "menu": VIEW,
    },

    "Site Supervisor": {
        "overview":         VIEW,
        "team":            NONE,
        "documents":             VIEW,
        "scope":      VIEW,
        "model":             VIEW,
        "meetings":           VIEW,
        "quantities":            NONE,
        "estimate":              VIEW,
        "programme":              NONE,
        "menu": NONE,
    },


    "Facility Manager": {
        "overview":         FULL,
        "team":            p(True, True, False, False, False, False),
        "documents":             p(True, False, False, False, False, False),
        "scope":      VIEW,
        "model":             NONE,
        "meetings":           NONE,
        "quantities":            NONE,
        "estimate":              NONE,
        "programme":              NONE,
        "menu": NONE,
    },

    "Maintenance Engineer": {
        "overview":         VIEW,
        "team":            NONE,
        "documents":             VIEW,
        "scope":      VIEW,
        "model":             NONE,
        "meetings":           NONE,
        "quantities":            NONE,
        "estimate":              NONE,
        "programme":              NONE,
        "menu": NONE,
    },
}



CDE_SUBMODULE_PERMISSIONS: dict[str, dict[str, dict]] = {

    "BIM Manager": {
        "wip":       FULL,
        "shared":    FULL,
        "published": FULL,
        "archived":  VIEW,
    },
    "Project Manager": {
        "wip":       p(True, True, True, False, True, False),
        "shared":    p(True, True, True, False, True, True),
        "published": p(True, False, False, False, True, True),
        "archived":  VIEW,
    },
    "Structural Engineer": {
        "wip":       p(True, True, True, False, True, True),
        "shared":    p(True, True, True, False, True, True),
        "published": VIEW,
        "archived":  VIEW,
    },
    "MEP Engineer": {
        "wip":       p(True, True, True, False, True, True),
        "shared":    p(True, True, True, False, True, True),
        "published": VIEW,
        "archived":  VIEW,
    },
    "Architect": {
        "wip":       p(True, True, True, False, True, True),
        "shared":    p(True, True, True, False, True, True),
        "published": VIEW,
        "archived":  VIEW,
    },
    "Civil Engineer": {
        "wip":       p(True, True, True, False, True, True),
        "shared":    p(True, True, True, False, True, True),
        "published": VIEW,
        "archived":  VIEW,
    },
    "Cost Consultant": {
        "wip":       NONE,
        "shared":    VIEW,
        "published": VIEW,
        "archived":  VIEW,
    },
    "Planning Engineer": {
        "wip":       NONE,
        "shared":    VIEW,
        "published": VIEW,
        "archived":  VIEW,
    },
    "Client Representative": {
        "wip":       NONE,
        "shared":    NONE,
        "published": p(True, False, False, False, True, False),
        "archived":  NONE,
    },
    "Client Viewer": {
        "wip":       NONE,
        "shared":    NONE,
        "published": VIEW,
        "archived":  NONE,
    },
    "Site Engineer": {
        "wip":       p(True, True, True, False, False, False),
        "shared":    VIEW,
        "published": VIEW,
        "archived":  NONE,
    },
    "Site Supervisor": {
        "wip":       NONE,
        "shared":    VIEW,
        "published": VIEW,
        "archived":  NONE,
    },
    "Facility Manager": {
        "wip":       NONE,
        "shared":    NONE,
        "published": VIEW,
        "archived":  VIEW,
    },
    "Maintenance Engineer": {
        "wip":       NONE,
        "shared":    NONE,
        "published": VIEW,
        "archived":  NONE,
    },
}


MENU_SUBMODULE_PERMISSIONS: dict[str, dict[str, dict]] = {

    "Owner": {
        "ids_maker":      FULL,
        "vendor":         FULL,
        "equipment":      FULL,
        "material":       FULL,
        "human_resource": FULL,
    },
    "Admin": {
        "ids_maker":      FULL,
        "vendor":         FULL,
        "equipment":      FULL,
        "material":       FULL,
        "human_resource": FULL,
    },
    "BIM Manager": {
        "ids_maker":      FULL,
        "vendor":         FULL,
        "equipment":      FULL,
        "material":       FULL,
        "human_resource": FULL,
    },
    "Project Manager": {
        "ids_maker":      FULL,
        "vendor":         p(True, True, True, False, True, True),
        "equipment":      p(True, True, True, False, True, True),
        "material":       p(True, True, True, False, True, True),
        "human_resource": p(True, True, True, False, True, True),
    },
    "Structural Engineer": {
        "ids_maker":      p(True, True, True, False, True, True),
        "vendor":         VIEW,
        "equipment":      VIEW,
        "material":       VIEW,
        "human_resource": VIEW,
    },
    "MEP Engineer": {
        "ids_maker":      p(True, True, True, False, True, True),
        "vendor":         VIEW,
        "equipment":      VIEW,
        "material":       VIEW,
        "human_resource": VIEW,
    },
    "Architect": {
        "ids_maker":      p(True, True, True, False, True, True),
        "vendor":         VIEW,
        "equipment":      VIEW,
        "material":       VIEW,
        "human_resource": VIEW,
    },
    "Civil Engineer": {
        "ids_maker":      p(True, True, True, False, True, True),
        "vendor":         VIEW,
        "equipment":      VIEW,
        "material":       VIEW,
        "human_resource": VIEW,
    },
    "Cost Consultant": {
        "ids_maker":      NONE,
        "vendor":         VIEW,
        "equipment":      VIEW,
        "material":       VIEW,
        "human_resource": NONE,
    },
    "Planning Engineer": {
        "ids_maker":      NONE,
        "vendor":         VIEW,
        "equipment":      VIEW,
        "material":       VIEW,
        "human_resource": NONE,
    },
    "Client Representative": {
        "ids_maker":      NONE,
        "vendor":         NONE,
        "equipment":      NONE,
        "material":       NONE,
        "human_resource": NONE,
    },
    "Client Viewer": {
        "ids_maker":      NONE,
        "vendor":         NONE,
        "equipment":      NONE,
        "material":       NONE,
        "human_resource": NONE,
    },
    "Site Engineer": {
        "ids_maker":      VIEW,
        "vendor":         VIEW,
        "equipment":      VIEW,
        "material":       VIEW,
        "human_resource": NONE,
    },
    "Site Supervisor": {
        "ids_maker":      NONE,
        "vendor":         VIEW,
        "equipment":      VIEW,
        "material":       VIEW,
        "human_resource": NONE,
    },
    "Facility Manager": {
        "ids_maker":      NONE,
        "vendor":         NONE,
        "equipment":      VIEW,
        "material":       VIEW,
        "human_resource": NONE,
    },
    "Maintenance Engineer": {
        "ids_maker":      NONE,
        "vendor":         NONE,
        "equipment":      VIEW,
        "material":       VIEW,
        "human_resource": NONE,
    },
}



async def seed_roles(session: AsyncSession) -> dict[str, uuid.UUID]:
    print("\n── Seeding roles ──")
    role_map: dict[str, uuid.UUID] = {}

    for r in ROLES_TO_SEED:
        existing = await session.scalar(
            select(Role).where(Role.name == r["name"], Role.deleted_at.is_(None))
        )
        if existing:
            print(f"  SKIP  {r['name']}")
            role_map[r["name"]] = existing.id
        else:
            role = Role(
                id=uuid.uuid4(),
                name=r["name"],
                description=r["description"],
                product_type=r["product_type"],
                is_system=r["is_system"],
                is_editable=r["is_editable"],
                is_active=True,
                created_by_type="system",
                workspace_id=None,
            )
            session.add(role)
            await session.flush()
            role_map[r["name"]] = role.id
            print(f"{r['name']}  ({r['product_type']})")

    return role_map


async def seed_modules(session: AsyncSession) -> dict[str, uuid.UUID]:
    print("\n── Seeding modules ──")
    module_map: dict[str, uuid.UUID] = {}

    for m in MODULES_TO_SEED:
        existing = await session.scalar(
            select(Module).where(Module.slug == m["slug"])
        )
        if existing:
            print(f"SKIP  {m['slug']}")
            module_map[m["slug"]] = existing.id
        else:
            module = Module(
                id=uuid.uuid4(),
                name=m["name"], slug=m["slug"],
                product_type=m["product_type"],
                order=m["order"], is_active=True,
            )
            session.add(module)
            await session.flush()
            module_map[m["slug"]] = module.id
            print(f"{m['slug']}  ({m['product_type']})")

    return module_map


async def seed_submodules(
    session: AsyncSession,
    module_map: dict[str, uuid.UUID],
) -> dict[str, uuid.UUID]:
    print("\n── Seeding submodules ──")
    submodule_map: dict[str, uuid.UUID] = {}

    # cde_id = module_map["cde"]
    # for s in CDE_SUBMODULES_TO_SEED:
    #     existing = await session.scalar(
    #         select(Submodule).where(
    #             Submodule.module_id == cde_id,
    #             Submodule.slug == s["slug"],
    #         )
    #     )
    #     if existing:
    #         print(f"  SKIP  cde/{s['slug']}")
    #         submodule_map[f"cde/{s['slug']}"] = existing.id
    #     else:
    #         sub = Submodule(
    #             id=uuid.uuid4(),
    #             module_id=cde_id,
    #             name=s["name"], slug=s["slug"],
    #             order=s["order"], is_active=True,
    #         )
    #         session.add(sub)
    #         await session.flush()
    #         submodule_map[f"cde/{s['slug']}"] = sub.id
    #         print(f"  ✓     cde/{s['slug']}")

    cde_id = module_map["documents"]
    for s in CDE_SUBMODULES_TO_SEED:
        existing = await session.scalar(
            select(Submodule).where(
                Submodule.module_id == cde_id,
                Submodule.slug == s["slug"],
            )
        )
        if existing:
            print(f"  SKIP  documents/{s['slug']}")
            submodule_map[f"documents/{s['slug']}"] = existing.id
        else:
            sub = Submodule(
                id=uuid.uuid4(),
                module_id=cde_id,
                name=s["name"], slug=s["slug"],
                order=s["order"], is_active=True,
            )
            session.add(sub)
            await session.flush()
            submodule_map[f"documents/{s['slug']}"] = sub.id
            print(f"  ✓     documents/{s['slug']}")

    menu_id = module_map["menu"]
    for s in MENU_SUBMODULES_TO_SEED:
        existing = await session.scalar(
            select(Submodule).where(
                Submodule.module_id == menu_id,
                Submodule.slug == s["slug"],
            )
        )
        if existing:
            print(f"  SKIP  menu/{s['slug']}")
            submodule_map[f"menu/{s['slug']}"] = existing.id
        else:
            sub = Submodule(
                id=uuid.uuid4(),
                module_id=menu_id,
                name=s["name"], slug=s["slug"],
                order=s["order"], is_active=True,
            )
            session.add(sub)
            await session.flush()
            submodule_map[f"menu/{s['slug']}"] = sub.id
            print(f"  ✓     menu/{s['slug']}")

    return submodule_map


async def seed_role_permissions(
    session: AsyncSession,
    role_map: dict[str, uuid.UUID],
    module_map: dict[str, uuid.UUID],
    submodule_map: dict[str, uuid.UUID],
) -> None:

    print("\n── Seeding module-level permissions ──")

    for role_name, modules in MODULE_PERMISSIONS.items():
        role_id = role_map.get(role_name)
        if not role_id:
            print(f"  WARN  role '{role_name}' not found, skipping")
            continue

        for module_slug, perms in modules.items():
            module_id = module_map.get(module_slug)
            if not module_id:
                print(f"  WARN  module '{module_slug}' not found, skipping")
                continue

            existing = await session.scalar(
                select(RolePermission).where(
                    RolePermission.role_id == role_id,
                    RolePermission.module_id == module_id,
                    RolePermission.submodule_id.is_(None),
                )
            )
            if existing:
                print(f"  SKIP  {role_name} × {module_slug}")
            else:
                session.add(RolePermission(
                    id=uuid.uuid4(),
                    role_id=role_id, module_id=module_id, submodule_id=None,
                    **perms,
                ))
                print(f"  ✓     {role_name} × {module_slug}")

    await session.flush()

    print("\n── Seeding CDE submodule permissions ──")
    cde_id = module_map["documents"]

    for role_name, submodules in CDE_SUBMODULE_PERMISSIONS.items():
        role_id = role_map.get(role_name)
        if not role_id:
            continue

        for sub_slug, perms in submodules.items():
            sub_id = submodule_map.get(f"documents/{sub_slug}")
            if not sub_id:
                print(f"  WARN  submodule 'documents/{sub_slug}' not found")
                continue

            existing = await session.scalar(
                select(RolePermission).where(
                    RolePermission.role_id == role_id,
                    RolePermission.module_id == cde_id,
                    RolePermission.submodule_id == sub_id,
                )
            )
            if existing:
                print(f"  SKIP  {role_name} × cde/{sub_slug}")
            else:
                session.add(RolePermission(
                    id=uuid.uuid4(),
                    role_id=role_id, module_id=cde_id, submodule_id=sub_id,
                    **perms,
                ))
                print(f"  ✓     {role_name} × cde/{sub_slug}")

    await session.flush()

    print("\n── Seeding Menu submodule permissions ──")
    menu_id = module_map["menu"]

    for role_name, submodules in MENU_SUBMODULE_PERMISSIONS.items():
        role_id = role_map.get(role_name)
        if not role_id:
            continue

        for sub_slug, perms in submodules.items():
            sub_id = submodule_map.get(f"menu/{sub_slug}")
            if not sub_id:
                print(f"  WARN  submodule 'menu/{sub_slug}' not found")
                continue

            existing = await session.scalar(
                select(RolePermission).where(
                    RolePermission.role_id == role_id,
                    RolePermission.module_id == menu_id,
                    RolePermission.submodule_id == sub_id,
                )
            )
            if existing:
                print(f"  SKIP  {role_name} × menu/{sub_slug}")
            else:
                session.add(RolePermission(
                    id=uuid.uuid4(),
                    role_id=role_id, module_id=menu_id, submodule_id=sub_id,
                    **perms,
                ))
                print(f"  ✓     {role_name} × menu/{sub_slug}")

    await session.flush()



async def main():
    print("=" * 55)
    print("  RBAC Seeder v2  —  starting")
    print("=" * 55)

    async with AsyncSessionLocal() as session:
        async with session.begin():
            role_map      = await seed_roles(session)
            module_map    = await seed_modules(session)
            submodule_map = await seed_submodules(session, module_map)
            await seed_role_permissions(session, role_map, module_map, submodule_map)

    print("\n" + "=" * 55)
    print("  RBAC Seeder  —  complete")
    print("=" * 55)


if __name__ == "__main__":
    asyncio.run(main())
