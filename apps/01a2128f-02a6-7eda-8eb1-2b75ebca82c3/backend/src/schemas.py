"""Pydantic request/response schemas for Asset Viewer.

Only imports from pydantic, typing, datetime, enum, and the standard library.
"""

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class AssetOut(BaseModel):
    """One cached Salesforce Asset. Nullable fields mirror Salesforce nulls."""

    id: str
    name: str
    account: str | None
    product_code: str | None
    family: str | None
    mrr: float | None
    lifecycle_value: float | None
    lifecycle_start: date | None
    lifecycle_end: date | None
    renewal_term: int | None
    renewal_unit: str | None
    owner: str | None
    created_date: datetime | None


class AssetSummary(BaseModel):
    asset_count: int
    total_lifecycle_value: float
    total_mrr: float
    synced_at: datetime | None


NoteText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
]


class NoteIn(BaseModel):
    text: NoteText


class NoteOut(BaseModel):
    id: int
    text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HealthOut(BaseModel):
    status: str
