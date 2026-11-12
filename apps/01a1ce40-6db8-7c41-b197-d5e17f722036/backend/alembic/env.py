import logging
import os
import sys
from importlib import import_module
from logging.config import fileConfig

from alembic.operations import ops
from pgvector.sqlalchemy import Vector
from sqlalchemy import text

from alembic import context

# Set up logging
logger = logging.getLogger(__name__)

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# Alembic Config object
config = context.config

# Set up logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from src.app_config import get_db_schema

# Get the target schema (required)
DB_SCHEMA = get_db_schema()

# Import the database setup and models
# The database connection is configured in src/database.py (DO NOT MODIFY)
# User models are defined in src/models.py
try:
    # Import models to ensure they're registered with Base.metadata
    import_module("src.models")
    from src.database import Base

    target_metadata = Base.metadata
except ImportError:
    # If models haven't been created yet, use empty metadata with naming convention
    from sqlalchemy import MetaData

    # Use the same naming convention as Base.metadata for consistency
    target_metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )
else:
    # Optional: src.sync registers the sync_jobs model used by the
    # building-data-syncs skill's runner. Apps that don't ship src/sync.py
    # raise ModuleNotFoundError(name="src.sync") here, which is a no-op.
    # Any other ImportError means src.sync exists but is broken — propagate
    # so autogenerate doesn't silently miss the sync_jobs table.
    try:
        import_module("src.sync")
    except ModuleNotFoundError as e:
        if e.name != "src.sync":
            raise


def include_object(object, name, type_, reflected, compare_to):
    """Exclude alembic_version table from autogenerate."""
    return not (type_ == "table" and name == "alembic_version")


def process_revision_directives(context, revision, directives):
    """
    Enforce migration-safety policies that are environment-independent:
    - Any new non-nullable column on an existing table MUST have a server_default.
    - An existing column may NOT be flipped to NOT NULL via autogenerate, because
      a server_default does not backfill rows already in the table, so the table
      rewrite fails on any existing NULL row (Postgres error 23502). The change
      must be a hand-written migration that backfills the NULLs before the ALTER.
    """

    # We only care about the 'upgrade' scripts
    for directive in directives:
        # The 'ops' attribute is a list of operations like AddColumnOp, etc.
        if hasattr(directive, "upgrade_ops") and directive.upgrade_ops:
            for op in directive.upgrade_ops.ops:
                # Check if it's a ModifyTableOps containing AddColumnOps
                if isinstance(op, ops.ModifyTableOps):
                    for sub_op in op.ops:
                        if isinstance(sub_op, ops.AddColumnOp):
                            column = sub_op.column
                            if not column.nullable and column.server_default is None:
                                # Raise an error if the policy is violated
                                raise ValueError(
                                    f"[Error] Attempting to add non-nullable column '{column.name}' to table '{op.table_name}' without a `server_default`.\n"
                                    f"\n"
                                    f"## Migration Safety Policy\n"
                                    f"All new non-nullable columns on existing tables must have a server-side default to prevent locking issues and migration failures in production.\n"
                                    f"\n"
                                    f"## Fix Required\n"
                                    f"Add a `server_default` to your SQLAlchemy model in `backend/src/models.py`:\n"
                                    f"\n"
                                    f"```python\n"
                                    f"# For string columns with default values\n"
                                    f"{column.name} = Column(String, nullable=False, server_default='active')\n"
                                    f"\n"
                                    f"# For timestamps\n"
                                    f"{column.name} = Column(DateTime(timezone=True), nullable=False, server_default=func.now())\n"
                                    f"\n"
                                    f"# For boolean columns\n"
                                    f"{column.name} = Column(Boolean, nullable=False, server_default=text('false'))\n"
                                    f"```\n"
                                    f"\n"
                                    f"Then run `alembic revision --autogenerate` again."
                                )
                            else:
                                logger.info(
                                    f"Policy check OK for column '{column.name}' on table '{op.table_name}'."
                                )
                        # Flipping an existing column to NOT NULL (modify_nullable is
                        # False) rewrites the table and errors on existing NULL rows.
                        # server_default only fills NEW rows, so it does not make this
                        # safe — the rows already in the table stay NULL.
                        elif (
                            isinstance(sub_op, ops.AlterColumnOp)
                            and sub_op.modify_nullable is False
                        ):
                            raise ValueError(
                                f"[Error] Attempting to set existing column '{sub_op.column_name}' on table '{sub_op.table_name}' to NOT NULL.\n"
                                f"\n"
                                f"## Migration Safety Policy\n"
                                f"Changing an existing column to NOT NULL rewrites the table and FAILS on any row that already holds NULL with `column ... contains null values` (Postgres error 23502). A `server_default` does not fix this: it only applies to new rows, never the rows already stored.\n"
                                f"\n"
                                f"## Fix Required\n"
                                f"Do not enforce NOT NULL through autogenerate. Write a manual migration that backfills the existing NULLs first, then sets NOT NULL:\n"
                                f"\n"
                                f"```python\n"
                                f"def upgrade():\n"
                                f'    op.execute("UPDATE {sub_op.table_name} SET {sub_op.column_name} = <default> WHERE {sub_op.column_name} IS NULL")\n'
                                f"    op.alter_column('{sub_op.table_name}', '{sub_op.column_name}', nullable=False)\n"
                                f"```\n"
                                f"\n"
                                f"If you cannot guarantee a safe backfill, keep the column nullable in `backend/src/models.py`."
                            )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        include_object=include_object,
        compare_type=True,
        compare_server_default=True,
        version_table_schema=DB_SCHEMA,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    # Use the engine from database.py which already has Cloud SQL configured
    from src.database import engine

    with engine.connect() as connection:
        # Set search_path to our schema (include public for extensions like pgvector)
        connection.execute(text(f'SET search_path TO "{DB_SCHEMA}", public'))
        connection.commit()

        connection.dialect.ischema_names["vector"] = Vector

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
            compare_server_default=True,
            version_table_schema=DB_SCHEMA,
            process_revision_directives=process_revision_directives,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
