"""SQLAlchemy models for Asset Viewer."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class CachedAsset(Base):
    """Local read-only cache of the latest Salesforce Asset query result."""

    __tablename__ = "cached_assets"
    __table_args__ = ({"info": {"ontology": "asset"}},)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sf_id: Mapped[str] = mapped_column(String(18), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_family: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_mrr: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    total_lifecycle_amount: Mapped[Decimal | None] = mapped_column(
        Numeric, nullable=True
    )
    lifecycle_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    lifecycle_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    renewal_term: Mapped[int | None] = mapped_column(Integer, nullable=True)
    renewal_term_unit: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sf_created_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_text("now()")
    )


class TestNote(Base):
    """Free-text note saved in the app database (independent of Salesforce)."""

    __tablename__ = "test_notes"
    __table_args__ = ({"info": {"ontology": "test-note"}},)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sql_text("now()")
    )
