"""Revenue Cloud product catalog API. Admin-only.

Read endpoints serve the local cache filled by the catalog sync. Only the
description endpoints reach Salesforce live: a single-record read for review
and the one confirmed Product2.Description write.
"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from src.auth import CurrentUser, require_role
from src.catalog import description_service, read_service
from src.catalog.salesforce_gateway import ProductGateway, get_product_gateway
from src.dependencies import get_db
from src.models import DescriptionChange
from src.schemas import (
    AttributeLibrary,
    CatalogOverview,
    CatalogSyncStatus,
    DescriptionChangeItem,
    DescriptionPreview,
    DescriptionPreviewRequest,
    DescriptionUpdateRequest,
    DescriptionUpdateResult,
    LiveDescription,
    ProductDetail,
    ProductLookupResponse,
    ProductPage,
)

router = APIRouter(prefix="/api/catalog", tags=["catalog"])

DbSession = Annotated[Session, Depends(get_db)]
Admin = Annotated[CurrentUser, Depends(require_role("admin"))]
Gateway = Annotated[ProductGateway, Depends(get_product_gateway)]
# Exact 18-character Salesforce Product2 ID (key prefix 01t).
ProductId = Annotated[
    str,
    Path(
        pattern=r"^01t[a-zA-Z0-9]{15}$",
        description="Exact 18-character Salesforce Product2 record ID",
    ),
]
OptionalSfId = Annotated[str | None, Query(pattern=r"^[a-zA-Z0-9]{18}$")]


@router.get("/overview", response_model=CatalogOverview)
def get_overview(db: DbSession, _: Admin) -> CatalogOverview:
    return read_service.overview(db)


@router.get("/sync-status", response_model=CatalogSyncStatus)
def get_sync_status(db: DbSession, _: Admin) -> CatalogSyncStatus:
    return read_service.sync_status(db)


@router.get("/products/", response_model=ProductPage)
def list_products(
    db: DbSession,
    _: Admin,
    q: Annotated[str | None, Query(max_length=200)] = None,
    catalog_id: OptionalSfId = None,
    category_id: OptionalSfId = None,
    classification_id: OptionalSfId = None,
    product_type: Literal["bundle", "simple"] | None = None,
    is_active: bool | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> ProductPage:
    return read_service.list_products(
        db,
        q=q,
        catalog_id=catalog_id,
        category_id=category_id,
        product_type=product_type,
        is_active=is_active,
        classification_id=classification_id,
        page=page,
        page_size=page_size,
    )


@router.get("/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: ProductId, db: DbSession, _: Admin) -> ProductDetail:
    rec = read_service.get_cached_product(db, product_id)
    if rec is None:
        raise HTTPException(
            status_code=404,
            detail=f"No product with Salesforce ID {product_id} in the synced catalog.",
        )
    return read_service.product_detail(db, rec)


@router.get("/attributes", response_model=AttributeLibrary)
def get_attribute_library(db: DbSession, _: Admin) -> AttributeLibrary:
    return read_service.attribute_library(db)


# --- Narrow lookup / preview / update API (also suitable for an assistant) ---


@router.get("/lookup/products/", response_model=ProductLookupResponse)
def lookup_products(
    db: DbSession,
    _: Admin,
    q: Annotated[str, Query(min_length=1, max_length=200)],
    limit: Annotated[int, Query(ge=1, le=25)] = 10,
) -> ProductLookupResponse:
    """Find products in the synced catalog by name, product code, description, or exact ID."""
    return read_service.lookup_products(db, q, limit)


@router.get("/products/{product_id}/description", response_model=LiveDescription)
def get_live_description(
    product_id: ProductId, db: DbSession, _: Admin, gateway: Gateway
) -> LiveDescription:
    """Read the current description and LastModifiedDate live from Salesforce."""
    return description_service.live_description(db, gateway, product_id)


@router.post(
    "/products/{product_id}/description/preview", response_model=DescriptionPreview
)
def preview_description(
    product_id: ProductId,
    payload: DescriptionPreviewRequest,
    db: DbSession,
    _: Admin,
    gateway: Gateway,
) -> DescriptionPreview:
    """Compare a proposed description with the live Salesforce value. Never writes."""
    return description_service.preview(
        db, gateway, product_id, payload.proposed_description
    )


@router.put(
    "/products/{product_id}/description", response_model=DescriptionUpdateResult
)
def update_description(
    product_id: ProductId,
    payload: DescriptionUpdateRequest,
    db: DbSession,
    admin: Admin,
    gateway: Gateway,
) -> DescriptionUpdateResult:
    """Write one confirmed description to Salesforce Product2.Description.

    Requires confirm=true and the LastModifiedDate returned by the live read or
    preview; answers 409 without writing if the record changed since then.
    """
    return description_service.apply_update(
        db, gateway, product_id, payload, admin.email
    )


@router.get(
    "/products/{product_id}/description/history",
    response_model=list[DescriptionChangeItem],
)
def description_history(
    product_id: ProductId, db: DbSession, _: Admin
) -> list[DescriptionChange]:
    return (
        db.query(DescriptionChange)
        .filter(DescriptionChange.product_sf_id == product_id)
        .order_by(DescriptionChange.created_at.desc(), DescriptionChange.id.desc())
        .limit(50)
        .all()
    )
