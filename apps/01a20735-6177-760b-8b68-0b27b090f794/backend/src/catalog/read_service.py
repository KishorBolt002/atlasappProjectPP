"""Cache-backed catalog reads. Never calls Salesforce."""

from __future__ import annotations

import math
import os
from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from src.catalog.objects import ALL_OBJECTS, SECTION_REQUIREMENTS
from src.catalog.salesforce_gateway import parse_sf_datetime
from src.catalog.sync_catalog import SYNC_TYPE
from src.models import CatalogObjectCoverage, CatalogRecord
from src.schemas import (
    AttributeCategoryItem,
    AttributeDefinitionItem,
    AttributeLibrary,
    BundleComponentItem,
    BundleGroupItem,
    BundleStructure,
    CatalogOverview,
    CatalogSummary,
    CatalogSyncStatus,
    CatalogTotals,
    CategoryMembership,
    CategoryNode,
    ClassificationAttributeItem,
    ClassificationItem,
    CoverageItem,
    PicklistItem,
    PicklistValueItem,
    PriceEntryItem,
    ProductAttributeItem,
    ProductDetail,
    ProductListItem,
    ProductLookupItem,
    ProductLookupResponse,
    ProductPage,
    RecordRef,
    SectionAvailability,
    SellingModelItem,
)
from src.sync import SyncJob

UNAVAILABLE = ("blocked", "not_available", "error")


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _f(rec: CatalogRecord, key: str) -> Any:
    return (rec.fields or {}).get(key)


def _str(rec: CatalogRecord, key: str) -> str | None:
    value = _f(rec, key)
    return None if value is None else str(value)


def _bool(rec: CatalogRecord, key: str) -> bool | None:
    value = _f(rec, key)
    return value if isinstance(value, bool) else None


def _int(rec: CatalogRecord, key: str) -> int | None:
    value = _f(rec, key)
    return (
        int(value)
        if isinstance(value, (int, float)) and not isinstance(value, bool)
        else None
    )


def _float(rec: CatalogRecord, key: str) -> float | None:
    value = _f(rec, key)
    return (
        float(value)
        if isinstance(value, (int, float)) and not isinstance(value, bool)
        else None
    )


def _dt(rec: CatalogRecord, key: str) -> datetime | None:
    return parse_sf_datetime(_f(rec, key))


def _ref(rec: CatalogRecord | None) -> RecordRef | None:
    if rec is None:
        return None
    return RecordRef(sf_id=rec.sf_id, name=rec.name, code=rec.code)


def _ref_by_id(index: dict[str, CatalogRecord], sf_id: Any) -> RecordRef | None:
    if not sf_id:
        return None
    rec = index.get(str(sf_id))
    if rec is None:
        return RecordRef(sf_id=str(sf_id))
    return _ref(rec)


def _by_name(refs: list[RecordRef]) -> list[RecordRef]:
    return sorted(refs, key=lambda r: (r.name or "").lower())


def _class_attrs_sorted(
    items: list[ClassificationAttributeItem],
) -> list[ClassificationAttributeItem]:
    return sorted(items, key=lambda a: (a.name or "").lower())


def _load(db: Session, object_api_name: str) -> list[CatalogRecord]:
    return list(
        db.scalars(
            select(CatalogRecord)
            .where(CatalogRecord.object_api_name == object_api_name)
            .order_by(CatalogRecord.name, CatalogRecord.sf_id)
        )
    )


def _load_where(
    db: Session, object_api_name: str, field: str, values: Iterable[str]
) -> list[CatalogRecord]:
    values = list({v for v in values if v})
    if not values:
        return []
    return list(
        db.scalars(
            select(CatalogRecord).where(
                CatalogRecord.object_api_name == object_api_name,
                CatalogRecord.fields[field].astext.in_(values),
            )
        )
    )


def _load_ids(db: Session, ids: Iterable[str]) -> dict[str, CatalogRecord]:
    ids = list({i for i in ids if i})
    if not ids:
        return {}
    return {
        r.sf_id: r
        for r in db.scalars(select(CatalogRecord).where(CatalogRecord.sf_id.in_(ids)))
    }


def _count(db: Session, object_api_name: str) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(CatalogRecord)
            .where(CatalogRecord.object_api_name == object_api_name)
        )
        or 0
    )


def salesforce_record_url(sf_id: str) -> str | None:
    domain = os.environ.get("CONNECTORS_SALESFORCE_DOMAIN")
    if not domain:
        return None
    return f"https://{domain}/{sf_id}"


def salesforce_instance_url() -> str | None:
    domain = os.environ.get("CONNECTORS_SALESFORCE_DOMAIN")
    return f"https://{domain}" if domain else None


# ---------------------------------------------------------------------------
# Sync status and coverage
# ---------------------------------------------------------------------------


def sync_status(db: Session) -> CatalogSyncStatus:
    last_success = (
        db.query(SyncJob)
        .filter(SyncJob.sync_type == SYNC_TYPE, SyncJob.status == "success")
        .order_by(SyncJob.finished_at.desc())
        .first()
    )
    last_job = (
        db.query(SyncJob)
        .filter(SyncJob.sync_type == SYNC_TYPE)
        .order_by(SyncJob.created_at.desc())
        .first()
    )
    return CatalogSyncStatus(
        has_synced=last_success is not None,
        last_synced_at=last_success.finished_at if last_success else None,
        last_job_status=last_job.status if last_job else None,
        last_job_mode=(last_job.cursor or {}).get("mode") if last_job else None,
        last_job_finished_at=last_job.finished_at if last_job else None,
        last_failure_reason=last_job.failure_reason if last_job else None,
    )


def coverage(db: Session) -> list[CoverageItem]:
    rows = {r.object_api_name: r for r in db.scalars(select(CatalogObjectCoverage))}
    items = []
    for obj in ALL_OBJECTS:
        row = rows.get(obj.api_name)
        if row is None:
            items.append(
                CoverageItem(
                    object_api_name=obj.api_name,
                    label=obj.label,
                    section=obj.section,
                    mapped=obj.mapped,
                    status="never_synced",
                    salesforce_count=None,
                    cached_count=0,
                    missing_fields=[],
                    detail="Not checked yet. Run a sync to read this object from Salesforce.",
                    checked_at=None,
                )
            )
            continue
        items.append(
            CoverageItem(
                object_api_name=row.object_api_name,
                label=row.label,
                section=row.section,
                mapped=row.mapped,
                status=row.status,  # ty: ignore[invalid-argument-type]
                salesforce_count=row.salesforce_count,
                cached_count=row.cached_count,
                missing_fields=list(row.missing_fields or []),
                detail=row.detail,
                checked_at=row.checked_at,
            )
        )
    return items


def sections(
    items: list[CoverageItem], names: Iterable[str] | None = None
) -> list[SectionAvailability]:
    by_name = {i.object_api_name: i for i in items}
    out = []
    for section, objects in SECTION_REQUIREMENTS.items():
        if names is not None and section not in names:
            continue
        rows = [by_name[o] for o in objects if o in by_name]
        blocked = [r for r in rows if r.status in UNAVAILABLE]
        never = [r for r in rows if r.status == "never_synced"]
        if blocked:
            status = blocked[0].status
            detail = "; ".join(
                f"{r.object_api_name}: {r.detail or r.status}" for r in blocked
            )
        elif never:
            status = "never_synced"
            detail = "Not synced yet."
        else:
            status = (
                "empty" if rows and all(r.status == "empty" for r in rows) else "synced"
            )
            detail = None
        out.append(
            SectionAvailability(
                section=section,
                available=not blocked and not never,
                status=status,
                blocked_objects=[r.object_api_name for r in blocked],
                detail=detail,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Catalog navigation
# ---------------------------------------------------------------------------


def _category_paths(categories: dict[str, CatalogRecord]) -> dict[str, list[str]]:
    paths: dict[str, list[str]] = {}

    def path(cid: str, seen: set[str]) -> list[str]:
        if cid in paths:
            return paths[cid]
        rec = categories.get(cid)
        if rec is None or cid in seen:
            return []
        parent = _str(rec, "ParentCategoryId")
        result = (path(parent, seen | {cid}) if parent else []) + [rec.name or cid]
        paths[cid] = result
        return result

    for cid in categories:
        path(cid, set())
    return paths


def category_descendants(categories: list[CatalogRecord], root_id: str) -> set[str]:
    children: dict[str, list[str]] = defaultdict(list)
    for c in categories:
        parent = _str(c, "ParentCategoryId")
        if parent:
            children[parent].append(c.sf_id)
    found = {root_id}
    stack = [root_id]
    while stack:
        for child in children.get(stack.pop(), []):
            if child not in found:
                found.add(child)
                stack.append(child)
    return found


def overview(db: Session) -> CatalogOverview:
    catalogs = _load(db, "ProductCatalog")
    categories = _load(db, "ProductCategory")
    memberships = _load(db, "ProductCategoryProduct")

    direct: dict[str, set[str]] = defaultdict(set)
    by_catalog_products: dict[str, set[str]] = defaultdict(set)
    for m in memberships:
        cat_id, prod_id = _str(m, "ProductCategoryId"), _str(m, "ProductId")
        if cat_id and prod_id:
            direct[cat_id].add(prod_id)
        catalog_id = _str(m, "CatalogId")
        if catalog_id and prod_id:
            by_catalog_products[catalog_id].add(prod_id)

    children: dict[str | None, list[CatalogRecord]] = defaultdict(list)
    for c in categories:
        children[_str(c, "ParentCategoryId")].append(c)

    def sort_key(c: CatalogRecord) -> tuple[int, str]:
        order = _int(c, "SortOrder")
        return (order if order is not None else 1_000_000, (c.name or "").lower())

    def build(c: CatalogRecord, seen: frozenset[str]) -> tuple[CategoryNode, set[str]]:
        kids = []
        products = set(direct.get(c.sf_id, set()))
        for child in sorted(children.get(c.sf_id, []), key=sort_key):
            if child.sf_id in seen:
                continue
            node, child_products = build(child, seen | {child.sf_id})
            kids.append(node)
            products |= child_products
        return (
            CategoryNode(
                sf_id=c.sf_id,
                name=c.name,
                code=c.code,
                description=_str(c, "Description"),
                sort_order=_int(c, "SortOrder"),
                is_navigational=_bool(c, "IsNavigational"),
                product_count=len(direct.get(c.sf_id, set())),
                total_product_count=len(products),
                children=kids,
            ),
            products,
        )

    category_ids = {c.sf_id for c in categories}
    roots_by_catalog: dict[str, list[CatalogRecord]] = defaultdict(list)
    for c in categories:
        parent = _str(c, "ParentCategoryId")
        if not parent or parent not in category_ids:
            roots_by_catalog[_str(c, "CatalogId") or ""].append(c)

    summaries = []
    for cat in catalogs:
        nodes = [
            build(c, frozenset({c.sf_id}))[0]
            for c in sorted(roots_by_catalog.get(cat.sf_id, []), key=sort_key)
        ]
        summaries.append(
            CatalogSummary(
                sf_id=cat.sf_id,
                name=cat.name,
                code=cat.code,
                description=_str(cat, "Description"),
                catalog_type=_str(cat, "CatalogType"),
                effective_start=_dt(cat, "EffectiveStartDate"),
                effective_end=_dt(cat, "EffectiveEndDate"),
                category_count=sum(
                    1 for c in categories if _str(c, "CatalogId") == cat.sf_id
                ),
                product_count=len(by_catalog_products.get(cat.sf_id, set())),
                categories=nodes,
            )
        )

    bundles = (
        db.scalar(
            select(func.count())
            .select_from(CatalogRecord)
            .where(
                CatalogRecord.object_api_name == "Product2",
                CatalogRecord.fields["Type"].astext == "Bundle",
            )
        )
        or 0
    )
    items = coverage(db)
    return CatalogOverview(
        sync=sync_status(db),
        totals=CatalogTotals(
            catalogs=len(catalogs),
            categories=len(categories),
            products=_count(db, "Product2"),
            classifications=_count(db, "ProductClassification"),
            attribute_definitions=_count(db, "AttributeDefinition"),
            price_books=_count(db, "Pricebook2"),
            bundles=bundles,
        ),
        catalogs=summaries,
        sections=sections(items),
        coverage=items,
        salesforce_instance_url=salesforce_instance_url(),
    )


# ---------------------------------------------------------------------------
# Product search and list
# ---------------------------------------------------------------------------


def _product_query(
    db: Session,
    q: str | None,
    catalog_id: str | None,
    category_id: str | None,
    product_type: str | None,
    is_active: bool | None,
    classification_id: str | None,
):
    stmt = select(CatalogRecord).where(CatalogRecord.object_api_name == "Product2")
    if q and q.strip():
        escaped = (
            q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        like = f"%{escaped}%"
        stmt = stmt.where(
            or_(
                CatalogRecord.name.ilike(like, escape="\\"),
                CatalogRecord.code.ilike(like, escape="\\"),
                CatalogRecord.fields["Description"].astext.ilike(like, escape="\\"),
                CatalogRecord.sf_id == q.strip(),
            )
        )
    if category_id or catalog_id:
        membership = select(CatalogRecord.fields["ProductId"].astext).where(
            CatalogRecord.object_api_name == "ProductCategoryProduct"
        )
        if category_id:
            ids = category_descendants(_load(db, "ProductCategory"), category_id)
            membership = membership.where(
                CatalogRecord.fields["ProductCategoryId"].astext.in_(ids)
            )
        if catalog_id:
            membership = membership.where(
                CatalogRecord.fields["CatalogId"].astext == catalog_id
            )
        stmt = stmt.where(CatalogRecord.sf_id.in_(membership))
    if product_type == "bundle":
        stmt = stmt.where(CatalogRecord.fields["Type"].astext == "Bundle")
    elif product_type == "simple":
        stmt = stmt.where(
            or_(
                CatalogRecord.fields["Type"].astext.is_(None),
                CatalogRecord.fields["Type"].astext != "Bundle",
            )
        )
    if is_active is not None:
        stmt = stmt.where(CatalogRecord.fields["IsActive"].as_boolean() == is_active)
    if classification_id:
        stmt = stmt.where(CatalogRecord.fields["BasedOnId"].astext == classification_id)
    return stmt


def _memberships_for(
    db: Session, product_ids: list[str]
) -> dict[str, list[CatalogRecord]]:
    out: dict[str, list[CatalogRecord]] = defaultdict(list)
    for m in _load_where(db, "ProductCategoryProduct", "ProductId", product_ids):
        pid = _str(m, "ProductId")
        if pid:
            out[pid].append(m)
    return out


def list_products(
    db: Session,
    *,
    q: str | None,
    catalog_id: str | None,
    category_id: str | None,
    product_type: str | None,
    is_active: bool | None,
    classification_id: str | None,
    page: int,
    page_size: int,
) -> ProductPage:
    stmt = _product_query(
        db, q, catalog_id, category_id, product_type, is_active, classification_id
    )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = list(
        db.scalars(
            stmt.order_by(func.lower(CatalogRecord.name), CatalogRecord.sf_id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    ids = [r.sf_id for r in rows]
    members = _memberships_for(db, ids)
    related = _load_ids(
        db,
        [str(_f(r, "BasedOnId")) for r in rows if _f(r, "BasedOnId")]
        + [str(_f(m, "ProductCategoryId")) for ms in members.values() for m in ms],
    )
    items = []
    for r in rows:
        cat_names = sorted(
            {
                related[c].name or c
                for m in members.get(r.sf_id, [])
                if (c := _str(m, "ProductCategoryId")) and c in related
            }
        )
        items.append(
            ProductListItem(
                sf_id=r.sf_id,
                name=r.name,
                product_code=r.code,
                type=_str(r, "Type"),
                family=_str(r, "Family"),
                is_active=_bool(r, "IsActive"),
                description=_str(r, "Description"),
                classification=_ref_by_id(related, _f(r, "BasedOnId")),
                category_names=cat_names,
                last_modified=r.sf_last_modified,
            )
        )
    return ProductPage(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, math.ceil(total / page_size)) if total else 1,
    )


def lookup_products(db: Session, q: str, limit: int) -> ProductLookupResponse:
    stmt = _product_query(db, q, None, None, None, None, None)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = list(db.scalars(stmt.order_by(func.lower(CatalogRecord.name)).limit(limit)))
    members = _memberships_for(db, [r.sf_id for r in rows])
    related = _load_ids(
        db,
        [
            str(_f(m, k))
            for ms in members.values()
            for m in ms
            for k in ("ProductCategoryId", "CatalogId")
            if _f(m, k)
        ],
    )
    items = []
    for r in rows:
        ms = members.get(r.sf_id, [])
        items.append(
            ProductLookupItem(
                sf_id=r.sf_id,
                name=r.name,
                product_code=r.code,
                type=_str(r, "Type"),
                is_active=_bool(r, "IsActive"),
                description=_str(r, "Description"),
                catalog_names=sorted(
                    {
                        related[c].name or c
                        for m in ms
                        if (c := _str(m, "CatalogId")) and c in related
                    }
                ),
                category_names=sorted(
                    {
                        related[c].name or c
                        for m in ms
                        if (c := _str(m, "ProductCategoryId")) and c in related
                    }
                ),
            )
        )
    return ProductLookupResponse(
        query=q,
        items=items,
        total_matches=total,
        last_synced_at=sync_status(db).last_synced_at,
    )


# ---------------------------------------------------------------------------
# Product detail
# ---------------------------------------------------------------------------


def get_cached_product(db: Session, sf_id: str) -> CatalogRecord | None:
    return db.scalar(
        select(CatalogRecord).where(
            CatalogRecord.sf_id == sf_id, CatalogRecord.object_api_name == "Product2"
        )
    )


def _picklist_values(values: list[CatalogRecord]) -> list[PicklistValueItem]:
    items = [
        PicklistValueItem(
            sf_id=v.sf_id,
            label=_str(v, "DisplayValue") or v.name,
            value=_str(v, "Value"),
            code=v.code,
            is_default=_bool(v, "IsDefault"),
            sequence=_float(v, "Sequence"),
            status=_str(v, "Status"),
        )
        for v in values
    ]
    return sorted(
        items,
        key=lambda i: (i.sequence if i.sequence is not None else 1e9, i.label or ""),
    )


def _picklist_index(
    db: Session, picklist_ids: Iterable[str]
) -> dict[str, list[CatalogRecord]]:
    out: dict[str, list[CatalogRecord]] = defaultdict(list)
    for v in _load_where(db, "AttributePicklistValue", "PicklistId", picklist_ids):
        pid = _str(v, "PicklistId")
        if pid:
            out[pid].append(v)
    return out


def _classification_chain(db: Session, classification_id: str | None) -> list[str]:
    """The product's classification followed by its ancestors (inherited attributes)."""
    if not classification_id:
        return []
    parents = {
        c.sf_id: _str(c, "ParentProductClassificationId")
        for c in _load(db, "ProductClassification")
    }
    chain: list[str] = []
    current: str | None = classification_id
    while current and current not in chain:
        chain.append(current)
        current = parents.get(current)
    return chain


def _component(
    rec: CatalogRecord, index: dict[str, CatalogRecord]
) -> BundleComponentItem:
    rel = index.get(_str(rec, "ProductRelationshipTypeId") or "")
    return BundleComponentItem(
        sf_id=rec.sf_id,
        child_product=_ref_by_id(index, _f(rec, "ChildProductId")),
        child_classification=_ref_by_id(index, _f(rec, "ChildProductClassificationId")),
        relationship_type=rel.name if rel else None,
        quantity=_float(rec, "Quantity"),
        min_quantity=_float(rec, "MinQuantity"),
        max_quantity=_float(rec, "MaxQuantity"),
        is_required=_bool(rec, "IsComponentRequired"),
        is_default=_bool(rec, "IsDefaultComponent"),
        is_quantity_editable=_bool(rec, "IsQuantityEditable"),
        price_included_in_bundle=_bool(rec, "DoesBundlePriceIncludeChild"),
        sequence=_int(rec, "Sequence"),
    )


def product_detail(db: Session, rec: CatalogRecord) -> ProductDetail:
    pid = rec.sf_id
    memberships = _load_where(db, "ProductCategoryProduct", "ProductId", [pid])
    pads = _load_where(db, "ProductAttributeDefinition", "Product2Id", [pid])
    groups = _load_where(db, "ProductComponentGroup", "ParentProductId", [pid])
    components = _load_where(db, "ProductRelatedComponent", "ParentProductId", [pid])
    parents = _load_where(db, "ProductRelatedComponent", "ChildProductId", [pid])
    psm_options = _load_where(db, "ProductSellingModelOption", "Product2Id", [pid])
    price_entries = _load_where(db, "PricebookEntry", "Product2Id", [pid])

    chain = _classification_chain(db, _str(rec, "BasedOnId"))
    class_attrs = _load_where(
        db, "ProductClassificationAttr", "ProductClassificationId", chain
    )

    categories = {c.sf_id: c for c in _load(db, "ProductCategory")}
    paths = _category_paths(categories)

    related_ids: set[str] = set(chain)
    for m in memberships:
        related_ids.update(
            filter(None, [_str(m, "CatalogId"), _str(m, "ProductCategoryId")])
        )
    for a in pads + class_attrs:
        related_ids.update(
            filter(
                None, [_str(a, "AttributeDefinitionId"), _str(a, "AttributeCategoryId")]
            )
        )
    for c in components:
        related_ids.update(
            filter(
                None,
                [
                    _str(c, "ChildProductId"),
                    _str(c, "ChildProductClassificationId"),
                    _str(c, "ProductRelationshipTypeId"),
                ],
            )
        )
    for c in parents:
        related_ids.update(filter(None, [_str(c, "ParentProductId")]))
    for o in psm_options:
        related_ids.update(filter(None, [_str(o, "ProductSellingModelId")]))
    for e in price_entries:
        related_ids.update(
            filter(None, [_str(e, "Pricebook2Id"), _str(e, "ProductSellingModelId")])
        )
    index = _load_ids(db, related_ids)
    index.update(categories)

    definitions = {
        k: v for k, v in index.items() if v.object_api_name == "AttributeDefinition"
    }
    picklists = _picklist_index(
        db,
        [str(_f(d, "PicklistId")) for d in definitions.values() if _f(d, "PicklistId")],
    )

    def attribute(a: CatalogRecord, source: str) -> ProductAttributeItem:
        definition = definitions.get(_str(a, "AttributeDefinitionId") or "")
        values = (
            picklists.get(_str(definition, "PicklistId") or "", [])
            if definition
            else []
        )
        name = _str(a, "AttributeNameOverride") or (
            (_str(definition, "Label") or definition.name) if definition else a.name
        )
        return ProductAttributeItem(
            sf_id=a.sf_id,
            source=source,  # ty: ignore[invalid-argument-type]
            name=name,
            definition=_ref(definition),
            data_type=_str(definition, "DataType") if definition else None,
            category=_ref_by_id(index, _f(a, "AttributeCategoryId")),
            default_value=_str(a, "DefaultValue")
            or (_str(definition, "DefaultValue") if definition else None),
            is_required=_bool(a, "IsRequired"),
            is_hidden=_bool(a, "IsHidden"),
            is_read_only=_bool(a, "IsReadOnly"),
            is_price_impacting=_bool(a, "IsPriceImpacting"),
            status=_str(a, "Status"),
            sequence=_int(a, "Sequence"),
            display_type=_str(a, "DisplayType"),
            picklist_values=_picklist_values(values),
            excluded_picklist_values=_str(a, "ExcludedPicklistValues"),
        )

    overridden = {_str(p, "ProductClassificationAttributeId") for p in pads}
    attrs = [attribute(p, "product") for p in pads] + [
        attribute(c, "classification") for c in class_attrs if c.sf_id not in overridden
    ]
    attrs.sort(
        key=lambda a: (
            a.sequence if a.sequence is not None else 1_000_000,
            (a.name or "").lower(),
        )
    )

    bundle = None
    if groups or components:
        by_group: dict[str | None, list[BundleComponentItem]] = defaultdict(list)
        group_ids = {g.sf_id for g in groups}
        for c in components:
            gid = _str(c, "ProductComponentGroupId")
            by_group[gid if gid in group_ids else None].append(_component(c, index))
        for comps in by_group.values():
            comps.sort(
                key=lambda x: (
                    x.sequence if x.sequence is not None else 1_000_000,
                    (x.child_product.name if x.child_product else "") or "",
                )
            )
        group_items = [
            BundleGroupItem(
                sf_id=g.sf_id,
                name=g.name,
                code=g.code,
                description=_str(g, "Description"),
                parent_group_id=_str(g, "ParentGroupId"),
                min_components=_int(g, "MinBundleComponents"),
                max_components=_int(g, "MaxBundleComponents"),
                sequence=_int(g, "Sequence"),
                components=by_group.get(g.sf_id, []),
            )
            for g in groups
        ]
        group_items.sort(
            key=lambda g: (
                g.sequence if g.sequence is not None else 1_000_000,
                g.name or "",
            )
        )
        bundle = BundleStructure(
            groups=group_items, ungrouped_components=by_group.get(None, [])
        )

    selling = []
    for o in psm_options:
        model = index.get(_str(o, "ProductSellingModelId") or "")
        selling.append(
            SellingModelItem(
                sf_id=o.sf_id,
                selling_model=_ref(model)
                if model
                else _ref_by_id(index, _f(o, "ProductSellingModelId")),
                selling_model_type=_str(model, "SellingModelType") if model else None,
                pricing_term=_int(model, "PricingTerm") if model else None,
                pricing_term_unit=_str(model, "PricingTermUnit") if model else None,
                status=_str(model, "Status") if model else None,
                is_default=_bool(o, "IsDefault"),
            )
        )
    selling.sort(key=lambda s: (s.selling_model.name if s.selling_model else "") or "")

    prices = []
    for e in price_entries:
        book = index.get(_str(e, "Pricebook2Id") or "")
        prices.append(
            PriceEntryItem(
                sf_id=e.sf_id,
                price_book=_ref_by_id(index, _f(e, "Pricebook2Id")),
                price_book_is_standard=_bool(book, "IsStandard") if book else None,
                unit_price=_float(e, "UnitPrice"),
                is_active=_bool(e, "IsActive"),
                use_standard_price=_bool(e, "UseStandardPrice"),
                selling_model=_ref_by_id(index, _f(e, "ProductSellingModelId")),
            )
        )
    prices.sort(
        key=lambda p: (
            not p.price_book_is_standard,
            (p.price_book.name if p.price_book else "") or "",
        )
    )

    member_items = [
        CategoryMembership(
            sf_id=m.sf_id,
            catalog=_ref_by_id(index, _f(m, "CatalogId")),
            category=_ref_by_id(index, _f(m, "ProductCategoryId")),
            category_path=paths.get(_str(m, "ProductCategoryId") or "", []),
        )
        for m in memberships
    ]
    member_items.sort(
        key=lambda m: ((m.catalog.name if m.catalog else "") or "", m.category_path)
    )

    used_in = {}
    for c in parents:
        ref = _ref_by_id(index, _f(c, "ParentProductId"))
        if ref:
            used_in[ref.sf_id] = ref

    return ProductDetail(
        sf_id=pid,
        name=rec.name,
        product_code=rec.code,
        description=_str(rec, "Description"),
        is_active=_bool(rec, "IsActive"),
        is_archived=_bool(rec, "IsArchived"),
        family=_str(rec, "Family"),
        type=_str(rec, "Type"),
        configure_during_sale=_str(rec, "ConfigureDuringSale"),
        stock_keeping_unit=_str(rec, "StockKeepingUnit"),
        quantity_unit_of_measure=_str(rec, "QuantityUnitOfMeasure"),
        specification_type=_str(rec, "SpecificationType"),
        decomposition_scope=_str(rec, "DecompositionScope"),
        usage_model_type=_str(rec, "UsageModelType"),
        is_assetizable=_bool(rec, "IsAssetizable"),
        is_sold_only_with_other_products=_bool(rec, "IsSoldOnlyWithOtherProds"),
        availability_date=_dt(rec, "AvailabilityDate"),
        discontinued_date=_dt(rec, "DiscontinuedDate"),
        end_of_life_date=_dt(rec, "EndOfLifeDate"),
        help_text=_str(rec, "HelpText"),
        display_url=_str(rec, "DisplayUrl"),
        last_modified=rec.sf_last_modified,
        synced_at=rec.synced_at,
        salesforce_url=salesforce_record_url(pid),
        classification=_ref_by_id(index, _f(rec, "BasedOnId")),
        memberships=member_items,
        attributes=attrs,
        bundle=bundle,
        used_in_bundles=_by_name(list(used_in.values())),
        selling_models=selling,
        price_entries=prices,
        sections=sections(coverage(db)),
    )


# ---------------------------------------------------------------------------
# Attribute library
# ---------------------------------------------------------------------------


def attribute_library(db: Session) -> AttributeLibrary:
    definitions = _load(db, "AttributeDefinition")
    categories = _load(db, "AttributeCategory")
    category_links = _load(db, "AttributeCategoryAttribute")
    picklists = _load(db, "AttributePicklist")
    values = _picklist_index(db, [p.sf_id for p in picklists])
    classifications = _load(db, "ProductClassification")
    class_attrs = _load(db, "ProductClassificationAttr")
    pads = _load(db, "ProductAttributeDefinition")

    def_index = {d.sf_id: d for d in definitions}
    cat_index = {c.sf_id: c for c in categories}
    pick_index = {p.sf_id: p for p in picklists}
    class_index = {c.sf_id: c for c in classifications}

    cats_for_def: dict[str, list[RecordRef]] = defaultdict(list)
    defs_for_cat: dict[str, list[RecordRef]] = defaultdict(list)
    for link in category_links:
        d, c = _str(link, "AttributeDefinitionId"), _str(link, "AttributeCategoryId")
        if d and c:
            if (cref := _ref_by_id(cat_index, c)) is not None:
                cats_for_def[d].append(cref)
            if (dref := _ref_by_id(def_index, d)) is not None:
                defs_for_cat[c].append(dref)

    class_count: dict[str, set[str]] = defaultdict(set)
    for a in class_attrs:
        d = _str(a, "AttributeDefinitionId")
        if d:
            class_count[d].add(_str(a, "ProductClassificationId") or "")
    product_count: dict[str, set[str]] = defaultdict(set)
    for p in pads:
        d = _str(p, "AttributeDefinitionId")
        if d:
            product_count[d].add(_str(p, "Product2Id") or "")

    products_per_class: dict[str, int] = defaultdict(int)
    for based_on in db.scalars(
        select(CatalogRecord.fields["BasedOnId"].astext).where(
            CatalogRecord.object_api_name == "Product2"
        )
    ):
        if based_on:
            products_per_class[based_on] += 1

    attrs_per_class: dict[str, list[ClassificationAttributeItem]] = defaultdict(list)
    for a in class_attrs:
        cid = _str(a, "ProductClassificationId")
        if not cid:
            continue
        definition = def_index.get(_str(a, "AttributeDefinitionId") or "")
        attrs_per_class[cid].append(
            ClassificationAttributeItem(
                sf_id=a.sf_id,
                name=_str(a, "AttributeNameOverride")
                or (
                    (_str(definition, "Label") or definition.name)
                    if definition
                    else a.name
                ),
                definition=_ref(definition),
                category=_ref_by_id(cat_index, _f(a, "AttributeCategoryId")),
                is_required=_bool(a, "IsRequired"),
                default_value=_str(a, "DefaultValue"),
                status=_str(a, "Status"),
            )
        )

    def_items = [
        AttributeDefinitionItem(
            sf_id=d.sf_id,
            name=d.name,
            label=_str(d, "Label"),
            code=d.code,
            developer_name=_str(d, "DeveloperName"),
            description=_str(d, "Description"),
            data_type=_str(d, "DataType"),
            is_active=_bool(d, "IsActive"),
            is_required=_bool(d, "IsRequired"),
            default_value=_str(d, "DefaultValue"),
            picklist=_ref_by_id(pick_index, _f(d, "PicklistId")),
            picklist_values=_picklist_values(
                values.get(_str(d, "PicklistId") or "", [])
            ),
            categories=_by_name(cats_for_def.get(d.sf_id, [])),
            classification_count=len(class_count.get(d.sf_id, set()) - {""}),
            product_count=len(product_count.get(d.sf_id, set()) - {""}),
        )
        for d in definitions
    ]
    cat_items = [
        AttributeCategoryItem(
            sf_id=c.sf_id,
            name=c.name,
            code=c.code,
            description=_str(c, "Description"),
            attributes=_by_name(defs_for_cat.get(c.sf_id, [])),
        )
        for c in categories
    ]
    pick_items = [
        PicklistItem(
            sf_id=p.sf_id,
            name=p.name,
            code=p.code,
            status=_str(p, "Status"),
            data_type=_str(p, "DataType"),
            values=_picklist_values(values.get(p.sf_id, [])),
        )
        for p in picklists
    ]
    class_items = [
        ClassificationItem(
            sf_id=c.sf_id,
            name=c.name,
            code=c.code,
            status=_str(c, "Status"),
            parent=_ref_by_id(class_index, _f(c, "ParentProductClassificationId")),
            product_count=int(products_per_class.get(c.sf_id, 0)),
            attributes=_class_attrs_sorted(attrs_per_class.get(c.sf_id, [])),
        )
        for c in classifications
    ]
    return AttributeLibrary(
        definitions=def_items,
        categories=cat_items,
        picklists=pick_items,
        classifications=class_items,
        sections=sections(
            coverage(db), ["classification", "attributes", "product_attributes"]
        ),
    )
