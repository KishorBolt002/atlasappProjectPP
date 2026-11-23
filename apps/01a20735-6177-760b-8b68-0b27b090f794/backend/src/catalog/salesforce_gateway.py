"""The only module that talks to Salesforce for the product catalog.

Cache-backed read endpoints never call this. It is used by the catalog sync
(paged reads) and by the description edit flow (live single-record read,
field metadata check, and the one confirmed write).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import format_datetime
from typing import Any, Protocol

from simple_salesforce import Salesforce
from simple_salesforce.api import SFType
from simple_salesforce.exceptions import SalesforceError

from src.clients.connectors.salesforce_client import get_salesforce_client

# v66.0 exposes Revenue Cloud catalog fields that the connector default
# (v59.0) does not; verified against the org's /services/data/ listing.
API_VERSION = "66.0"

PRODUCT_ID_PATTERN = re.compile(r"^01t[a-zA-Z0-9]{15}$")
SF_ID_PATTERN = re.compile(r"^[a-zA-Z0-9]{18}$")


def connect() -> Salesforce:
    base = get_salesforce_client()
    return Salesforce(
        session_id=base.session_id, instance=base.sf_instance, version=API_VERSION
    )


def sobject(sf: Salesforce, api_name: str) -> SFType:
    """Typed handle for one sObject's REST resource."""
    return SFType(
        api_name,
        sf.session_id,
        sf.sf_instance,
        sf.sf_version,
        session=sf.session,
        salesforce=sf,
    )


def parse_sf_datetime(value: Any) -> datetime | None:
    """Parse Salesforce datetimes (`2026-11-07T09:53:06.000+0000`) and dates.

    Returns None for empty or unrecognized values instead of raising.
    """
    if not value or not isinstance(value, str):
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def soql_datetime(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def salesforce_error_text(exc: SalesforceError) -> str:
    """Render Salesforce's own error codes and messages for the user."""
    content = exc.content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                code = item.get("errorCode", "ERROR")
                msg = str(item.get("message", "")).strip()
                fields = item.get("fields") or []
                suffix = f" (fields: {', '.join(fields)})" if fields else ""
                parts.append(f"{code}: {msg}{suffix}")
        if parts:
            return "; ".join(parts)
    if isinstance(content, (str, bytes)) and content:
        text = content.decode() if isinstance(content, bytes) else content
        return text[:500]
    return f"Salesforce responded with HTTP {exc.status}"


@dataclass
class LiveProduct:
    sf_id: str
    name: str | None
    description: str | None
    last_modified: datetime
    system_modstamp: datetime | None
    last_modified_by: str | None


@dataclass
class FieldMetadata:
    object_api_name: str
    field_api_name: str
    label: str
    type: str
    length: int
    updateable: bool


class WriteConflictError(Exception):
    """Salesforce rejected the write because the record changed (HTTP 412)."""


class ProductGateway(Protocol):
    def read_product(self, sf_id: str) -> LiveProduct | None: ...

    def description_field(self) -> FieldMetadata | None: ...

    def write_description(
        self, sf_id: str, description: str | None, unmodified_since: datetime
    ) -> None: ...


class SalesforceProductGateway:
    """Live Product2 access through the shared Salesforce connector user."""

    def __init__(self) -> None:
        self._sf: Salesforce | None = None

    def _client(self) -> Salesforce:
        if self._sf is None:
            self._sf = connect()
        return self._sf

    def read_product(self, sf_id: str) -> LiveProduct | None:
        if not PRODUCT_ID_PATTERN.match(sf_id):
            raise ValueError("Expected an 18-character Salesforce Product2 ID")
        result = self._client().query(
            "SELECT Id, Name, Description, LastModifiedDate, SystemModstamp, "
            f"LastModifiedBy.Name FROM Product2 WHERE Id = '{sf_id}'"
        )
        records = result.get("records") or []
        if not records:
            return None
        rec = records[0]
        last_modified = parse_sf_datetime(rec.get("LastModifiedDate"))
        if last_modified is None:
            raise RuntimeError("Salesforce returned a product without LastModifiedDate")
        modified_by = rec.get("LastModifiedBy") or {}
        return LiveProduct(
            sf_id=rec["Id"],
            name=rec.get("Name"),
            description=rec.get("Description"),
            last_modified=last_modified,
            system_modstamp=parse_sf_datetime(rec.get("SystemModstamp")),
            last_modified_by=modified_by.get("Name")
            if isinstance(modified_by, dict)
            else None,
        )

    def description_field(self) -> FieldMetadata | None:
        describe = sobject(self._client(), "Product2").describe()
        for field in describe["fields"]:
            if field["name"] == "Description":
                return FieldMetadata(
                    object_api_name="Product2",
                    field_api_name="Description",
                    label=field["label"],
                    type=field["type"],
                    length=int(field["length"]),
                    updateable=bool(field["updateable"])
                    and bool(describe["updateable"]),
                )
        return None

    def write_description(
        self, sf_id: str, description: str | None, unmodified_since: datetime
    ) -> None:
        # Salesforce compares If-Unmodified-Since with the record's
        # LastModifiedDate and answers 412 when it changed after our read.
        header = format_datetime(unmodified_since.astimezone(UTC), usegmt=True)
        try:
            sobject(self._client(), "Product2").update(
                sf_id,
                {"Description": description},
                headers={"If-Unmodified-Since": header},
            )
        except SalesforceError as exc:
            if exc.status == 412:
                raise WriteConflictError(salesforce_error_text(exc)) from exc
            raise


def get_product_gateway() -> ProductGateway:
    """FastAPI dependency; tests override it with an in-memory fake."""
    return SalesforceProductGateway()
