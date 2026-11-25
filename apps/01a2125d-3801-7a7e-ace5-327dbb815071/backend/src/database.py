"""
CRITICAL: DO NOT MODIFY THIS FILE - CORE DATABASE CONNECTION SETUP
This file contains the essential database connection configuration required for
the application to connect to Google Cloud SQL (GCP), RDS (AWS), or Azure
Database for PostgreSQL Flexible Server. Any modifications to this file will
break the database connection.

If you need to add models, modify src/models.py instead.
"""

import os
from pathlib import Path

from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.app_config import get_db_schema
from src.clients.azure_credential import build_azure_credential

AZURE_POSTGRES_TOKEN_SCOPE = "https://ossrdbms-aad.database.windows.net/.default"

# Every app runs as a single container, and in the sandbox many apps share one
# small Postgres instance (50 slots on the shared-core tier). SQLAlchemy keeps
# pool_size connections open indefinitely once a burst has created them, so the
# default of 5 per container saturated the shared instance with idle connections
# and failed startup for the next service. Retain 2 instead, and keep the total
# at SQLAlchemy's default of 15 so request concurrency is unchanged.
DB_POOL_SIZE = 2
DB_POOL_MAX_OVERFLOW = 13

# Every statement on these connections fails once it runs longer than this.
# Postgres keeps running a statement after its client has stopped waiting, and no
# response is waited on for longer than this, so a longer statement would only
# hold database CPU that other requests need.
DB_STATEMENT_TIMEOUT = "600s"


def _load_db_password():
    password = os.environ.get("DB_PASSWORD", "")
    password_file = os.environ.get("DB_PASSWORD_FILE", "")
    if not password and password_file:
        secret_path = Path(password_file)
        if secret_path.exists():
            password = secret_path.read_text().strip()
    return password


def get_engine():
    """Get the database engine for the active cloud provider.

    AWS connects with the static credential mounted from Secrets Manager.
    Azure uses Microsoft Entra ID: a managed-identity token is fetched at
    connect time and passed in the libpq password slot.
    GCP connects via the Cloud SQL Python Connector with IAM authentication.
    """
    cloud_provider = os.environ.get("CLOUD_PROVIDER")
    if not cloud_provider:
        raise RuntimeError("CLOUD_PROVIDER is required")
    cloud_provider = cloud_provider.lower()

    # The local check runs first so workspace alembic (Cloud Run sidecar with
    # `DB_CONNECTION_TYPE=local`) hits the in-container Postgres regardless of
    # which cloud the app's services target. Only the Sandbox and Production
    # services, which set no connection type, reach the cloud-specific branches.
    if os.environ.get("DB_CONNECTION_TYPE") == "local" or cloud_provider == "aws":
        host = os.environ["DB_HOST"]
        port = os.environ["DB_PORT"]
        user = os.environ["DB_USER"]
        password = _load_db_password()
        db_name = os.environ["DB_NAME"]
        engine = create_engine(
            f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}",
            pool_pre_ping=True,
            pool_size=DB_POOL_SIZE,
            max_overflow=DB_POOL_MAX_OVERFLOW,
        )
    elif cloud_provider == "azure":
        host = os.environ["DB_HOST"]
        port = os.environ["DB_PORT"]
        user = os.environ["DB_USER"]
        db_name = os.environ["DB_NAME"]
        credential = build_azure_credential()
        engine = create_engine(
            f"postgresql+psycopg://{user}@{host}:{port}/{db_name}?sslmode=require",
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_size=DB_POOL_SIZE,
            max_overflow=DB_POOL_MAX_OVERFLOW,
        )

        # Fetch a fresh Entra token on every new physical connection; the
        # azure-identity credential caches/refreshes the token internally.
        @event.listens_for(engine, "do_connect")
        def provide_azure_token(dialect, conn_rec, cargs, cparams):
            cparams["password"] = credential.get_token(AZURE_POSTGRES_TOKEN_SCOPE).token

    elif cloud_provider == "gcp":
        # Cloud SQL with Private Service Access. The Cloud SQL Python Connector
        # only supports pg8000 / asyncpg / pymysql, so pg8000 is required here
        # — unlike AWS/Azure which use psycopg.
        connector = Connector()

        def get_conn():
            return connector.connect(
                os.environ["INSTANCE_CONNECTION_NAME"],
                "pg8000",
                user=os.environ["DB_USER"],
                db=os.environ["DB_NAME"],
                enable_iam_auth=True,
                ip_type=IPTypes.PRIVATE,
            )

        engine = create_engine(
            "postgresql+pg8000://",
            creator=get_conn,
            pool_pre_ping=True,
            pool_size=DB_POOL_SIZE,
            max_overflow=DB_POOL_MAX_OVERFLOW,
        )
    else:
        raise RuntimeError(f"Unsupported CLOUD_PROVIDER: {cloud_provider}")

    # Set the schema search path for multi-tenancy (always required)
    db_schema = get_db_schema()

    @event.listens_for(engine, "connect", insert=True)
    def configure_session(dbapi_conn, connection_record):
        existing_autocommit = dbapi_conn.autocommit
        dbapi_conn.autocommit = True
        cursor = dbapi_conn.cursor()
        # Set search path to use the app-specific schema (include public for extensions like pgvector)
        # nosemgrep: python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query, python.lang.security.audit.formatted-sql-query.formatted-sql-query -- schema name is derived from the app id or set by the platform, and a SET statement cannot take bind parameters
        cursor.execute(f'SET search_path TO "{db_schema}", public')
        # nosemgrep: python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query, python.lang.security.audit.formatted-sql-query.formatted-sql-query -- interpolates the module constant DB_STATEMENT_TIMEOUT, and a SET statement cannot take bind parameters
        cursor.execute(f"SET statement_timeout TO '{DB_STATEMENT_TIMEOUT}'")
        cursor.close()
        dbapi_conn.autocommit = existing_autocommit

    return engine


# Create the engine and session factory
engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


# Naming convention for database constraints
# This ensures Alembic can properly track and name constraints in migrations
convention = {
    "ix": "ix_%(table_name)s_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# Base class for all models
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    All models should inherit from this class.
    """

    metadata = MetaData(naming_convention=convention)
