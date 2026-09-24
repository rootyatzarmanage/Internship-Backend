import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from ycpa.core.config import get_settings
from ycpa.core.database.base import Base

from ycpa.models import (
    User,
    StorageUsage,
    PimSubscription,
    AimSubscription,
    SubscriptionPlan,
    Role,
    CdeFile,
    CdeFileShare,
    CdeFolder,
    CdePendingFileShare,
    CdeFolderShare,
    CdePendingFolderShare,
    IfcImport,
    IfcElement,
    Invitation,
    PimWorkspace,
    PimWorkspaceMember,
    PimProject,
    PimProjectMember,
    PimProjectFile,
    AimWorkspace,
    AimWorkspaceMember,
    AimProject,
    AimProjectMember,
    AimProjectFile,
    AuditLog,
    Module,
    Submodule,
    RolePermission,
    PimScopeDiscipline,
    PimScopeItem,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    settings = get_settings()

    context.configure(
        url=str(settings.DATABASE_URL_SYNC),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    settings = get_settings()

    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = str(settings.DATABASE_URL_SYNC)

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()