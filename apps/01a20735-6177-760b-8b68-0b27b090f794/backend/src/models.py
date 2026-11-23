"""
Database models for the application.

This file contains all SQLAlchemy models. You can freely add, modify, or remove
models in this file. The database connection and configuration is handled in
database.py and should not be modified.

Example model:

    from sqlalchemy import Column, Integer, String, Boolean, DateTime
    from sqlalchemy.sql import func
    from .database import Base

    class Todo(Base):
        __tablename__ = "todos"

        id = Column(Integer, primary_key=True, index=True)
        title = Column(String, index=True)
        description = Column(String, nullable=True)
        completed = Column(Boolean, default=False)
        created_at = Column(DateTime(timezone=True), server_default=func.now())
        updated_at = Column(DateTime(timezone=True), onupdate=func.now())
"""


# Add your models below this line
# All models should inherit from Base imported from database.py

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.database import Base


class Note(Base):
    __tablename__ = "notes"
    __table_args__ = ({"info": {"ontology": "note"}},)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AppUser(Base):
    """App-level role assignment. Authentication is handled by the platform."""

    __tablename__ = "app_users"
    __table_args__ = ({"info": {"ontology": "app_user"}},)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, server_default=text("''")
    )
    role: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'viewer'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class CatalogRecord(Base):
    """Local read cache of one Salesforce Revenue Cloud catalog record.

    Salesforce is the source of truth; rows are written only by the catalog
    sync and by the verified reload after a confirmed description update.
    """

    __tablename__ = "catalog_records"
    __table_args__ = (
        Index("ix_catalog_records_object_name", "object_api_name", "name"),
        {"info": {"ontology": "catalog_record"}},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sf_id: Mapped[str] = mapped_column(String(18), unique=True, nullable=False)
    object_api_name: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    fields: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    sf_last_modified: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sf_system_modstamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sync_token: Mapped[str | None] = mapped_column(String(36), nullable=True)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CatalogObjectCoverage(Base):
    """Per-object result of the last catalog sync: accessible, empty, or blocked."""

    __tablename__ = "catalog_object_coverage"
    __table_args__ = ({"info": {"ontology": "catalog_object_coverage"}},)

    object_api_name: Mapped[str] = mapped_column(String(80), primary_key=True)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    section: Mapped[str] = mapped_column(String(40), nullable=False)
    mapped: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    salesforce_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cached_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    missing_fields: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class DescriptionChange(Base):
    """Audit trail of every attempted Product2.Description write-back."""

    __tablename__ = "description_changes"
    __table_args__ = (
        Index("ix_description_changes_product", "product_sf_id", "created_at"),
        {"info": {"ontology": "description_change"}},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_sf_id: Mapped[str] = mapped_column(String(18), nullable=False)
    product_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_description: Mapped[str] = mapped_column(Text, nullable=False)
    expected_last_modified: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    salesforce_last_modified_after: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    requested_by: Mapped[str] = mapped_column(String(320), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
