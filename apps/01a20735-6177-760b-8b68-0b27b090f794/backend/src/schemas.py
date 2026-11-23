"""
Pydantic schemas for API request/response validation.

IMPORTANT: Never import from models, crud, services, or routers in this file.
Only import from pydantic, typing, datetime, enum, and standard library.

Example schemas:

    from pydantic import BaseModel, Field, ConfigDict
    from typing import Optional
    from datetime import datetime

    class TodoBase(BaseModel):
        title: str = Field(..., min_length=1, max_length=200)
        description: Optional[str] = None
        completed: bool = False

    class TodoCreate(TodoBase):
        pass

    class TodoUpdate(BaseModel):
        title: Optional[str] = Field(None, min_length=1, max_length=200)
        description: Optional[str] = None
        completed: Optional[bool] = None

    class TodoResponse(TodoBase):
        id: int
        created_at: datetime
        updated_at: Optional[datetime] = None

        model_config = ConfigDict(from_attributes=True)
"""


# Add your schemas below this line
# Follow the pattern: Base, Create, Update, Response for each model

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

NoteTitle = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
NoteBody = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)
]


class NoteCreate(BaseModel):
    title: NoteTitle
    body: NoteBody


class NoteUpdate(BaseModel):
    title: NoteTitle
    body: NoteBody


class NoteResponse(BaseModel):
    id: int
    title: str
    body: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Users and roles
# ---------------------------------------------------------------------------

UserRole = Literal["admin", "viewer"]


class UserCreate(BaseModel):
    email: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=3, max_length=320)
    ]
    name: Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] = ""
    role: UserRole = "viewer"

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        if "@" not in value:
            raise ValueError("Enter a valid email address")
        return value.lower()


class UserUpdate(BaseModel):
    name: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None
    ) = None
    role: UserRole


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeResponse(BaseModel):
    email: str
    name: str
    role: str
    is_admin: bool


# ---------------------------------------------------------------------------
# Revenue Cloud product catalog (read from the local cache)
# ---------------------------------------------------------------------------

CoverageStatus = Literal[
    "synced", "empty", "not_mapped", "not_available", "blocked", "error", "never_synced"
]


class RecordRef(BaseModel):
    sf_id: str
    name: str | None = None
    code: str | None = None


class CoverageItem(BaseModel):
    object_api_name: str
    label: str
    section: str
    mapped: bool
    status: CoverageStatus
    salesforce_count: int | None
    cached_count: int
    missing_fields: list[str]
    detail: str | None
    checked_at: datetime | None


class SectionAvailability(BaseModel):
    section: str
    available: bool
    status: CoverageStatus
    blocked_objects: list[str]
    detail: str | None


class CatalogSyncStatus(BaseModel):
    has_synced: bool
    last_synced_at: datetime | None
    last_job_status: str | None
    last_job_mode: str | None
    last_job_finished_at: datetime | None
    last_failure_reason: str | None


class CategoryNode(BaseModel):
    sf_id: str
    name: str | None
    code: str | None
    description: str | None
    sort_order: int | None
    is_navigational: bool | None
    product_count: int
    total_product_count: int
    children: list["CategoryNode"]


class CatalogSummary(BaseModel):
    sf_id: str
    name: str | None
    code: str | None
    description: str | None
    catalog_type: str | None
    effective_start: datetime | None
    effective_end: datetime | None
    category_count: int
    product_count: int
    categories: list[CategoryNode]


class CatalogTotals(BaseModel):
    catalogs: int
    categories: int
    products: int
    classifications: int
    attribute_definitions: int
    price_books: int
    bundles: int


class CatalogOverview(BaseModel):
    sync: CatalogSyncStatus
    totals: CatalogTotals
    catalogs: list[CatalogSummary]
    sections: list[SectionAvailability]
    coverage: list[CoverageItem]
    salesforce_instance_url: str | None


class ProductListItem(BaseModel):
    sf_id: str
    name: str | None
    product_code: str | None
    type: str | None
    family: str | None
    is_active: bool | None
    description: str | None
    classification: RecordRef | None
    category_names: list[str]
    last_modified: datetime | None


class ProductPage(BaseModel):
    items: list[ProductListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class PicklistValueItem(BaseModel):
    sf_id: str
    label: str | None
    value: str | None
    code: str | None
    is_default: bool | None
    sequence: float | None
    status: str | None


class ProductAttributeItem(BaseModel):
    sf_id: str
    source: Literal["product", "classification"]
    name: str | None
    definition: RecordRef | None
    data_type: str | None
    category: RecordRef | None
    default_value: str | None
    is_required: bool | None
    is_hidden: bool | None
    is_read_only: bool | None
    is_price_impacting: bool | None
    status: str | None
    sequence: int | None
    display_type: str | None
    picklist_values: list[PicklistValueItem]
    excluded_picklist_values: str | None


class CategoryMembership(BaseModel):
    sf_id: str
    catalog: RecordRef | None
    category: RecordRef | None
    category_path: list[str]


class BundleComponentItem(BaseModel):
    sf_id: str
    child_product: RecordRef | None
    child_classification: RecordRef | None
    relationship_type: str | None
    quantity: float | None
    min_quantity: float | None
    max_quantity: float | None
    is_required: bool | None
    is_default: bool | None
    is_quantity_editable: bool | None
    price_included_in_bundle: bool | None
    sequence: int | None


class BundleGroupItem(BaseModel):
    sf_id: str
    name: str | None
    code: str | None
    description: str | None
    parent_group_id: str | None
    min_components: int | None
    max_components: int | None
    sequence: int | None
    components: list[BundleComponentItem]


class BundleStructure(BaseModel):
    groups: list[BundleGroupItem]
    ungrouped_components: list[BundleComponentItem]


class SellingModelItem(BaseModel):
    sf_id: str
    selling_model: RecordRef | None
    selling_model_type: str | None
    pricing_term: int | None
    pricing_term_unit: str | None
    status: str | None
    is_default: bool | None


class PriceEntryItem(BaseModel):
    sf_id: str
    price_book: RecordRef | None
    price_book_is_standard: bool | None
    unit_price: float | None
    is_active: bool | None
    use_standard_price: bool | None
    selling_model: RecordRef | None


class ProductDetail(BaseModel):
    sf_id: str
    name: str | None
    product_code: str | None
    description: str | None
    is_active: bool | None
    is_archived: bool | None
    family: str | None
    type: str | None
    configure_during_sale: str | None
    stock_keeping_unit: str | None
    quantity_unit_of_measure: str | None
    specification_type: str | None
    decomposition_scope: str | None
    usage_model_type: str | None
    is_assetizable: bool | None
    is_sold_only_with_other_products: bool | None
    availability_date: datetime | None
    discontinued_date: datetime | None
    end_of_life_date: datetime | None
    help_text: str | None
    display_url: str | None
    last_modified: datetime | None
    synced_at: datetime
    salesforce_url: str | None
    classification: RecordRef | None
    memberships: list[CategoryMembership]
    attributes: list[ProductAttributeItem]
    bundle: BundleStructure | None
    used_in_bundles: list[RecordRef]
    selling_models: list[SellingModelItem]
    price_entries: list[PriceEntryItem]
    sections: list[SectionAvailability]


class ClassificationAttributeItem(BaseModel):
    sf_id: str
    name: str | None
    definition: RecordRef | None
    category: RecordRef | None
    is_required: bool | None
    default_value: str | None
    status: str | None


class ClassificationItem(BaseModel):
    sf_id: str
    name: str | None
    code: str | None
    status: str | None
    parent: RecordRef | None
    product_count: int
    attributes: list[ClassificationAttributeItem]


class AttributeDefinitionItem(BaseModel):
    sf_id: str
    name: str | None
    label: str | None
    code: str | None
    developer_name: str | None
    description: str | None
    data_type: str | None
    is_active: bool | None
    is_required: bool | None
    default_value: str | None
    picklist: RecordRef | None
    picklist_values: list[PicklistValueItem]
    categories: list[RecordRef]
    classification_count: int
    product_count: int


class AttributeCategoryItem(BaseModel):
    sf_id: str
    name: str | None
    code: str | None
    description: str | None
    attributes: list[RecordRef]


class PicklistItem(BaseModel):
    sf_id: str
    name: str | None
    code: str | None
    status: str | None
    data_type: str | None
    values: list[PicklistValueItem]


class AttributeLibrary(BaseModel):
    definitions: list[AttributeDefinitionItem]
    categories: list[AttributeCategoryItem]
    picklists: list[PicklistItem]
    classifications: list[ClassificationItem]
    sections: list[SectionAvailability]


class ProductLookupItem(BaseModel):
    sf_id: str
    name: str | None
    product_code: str | None
    type: str | None
    is_active: bool | None
    description: str | None
    catalog_names: list[str]
    category_names: list[str]


class ProductLookupResponse(BaseModel):
    query: str
    items: list[ProductLookupItem]
    total_matches: int
    last_synced_at: datetime | None


# ---------------------------------------------------------------------------
# Product description write-back (live Salesforce)
# ---------------------------------------------------------------------------

ProposedDescription = Annotated[str, StringConstraints(max_length=32000)]


class FieldMetadataOut(BaseModel):
    object_api_name: str
    field_api_name: str
    label: str
    type: str
    max_length: int
    updateable: bool


class LiveDescription(BaseModel):
    product_sf_id: str
    product_name: str | None
    current_description: str | None
    last_modified: datetime
    last_modified_by: str | None
    field: FieldMetadataOut
    cached_description: str | None
    cache_was_stale: bool


class DescriptionPreviewRequest(BaseModel):
    proposed_description: ProposedDescription


class DescriptionPreview(BaseModel):
    product_sf_id: str
    product_name: str | None
    current_description: str | None
    proposed_description: str
    changed: bool
    clears_description: bool
    proposed_length: int
    max_length: int
    writable: bool
    last_modified: datetime
    problems: list[str]
    can_apply: bool


class DescriptionUpdateRequest(BaseModel):
    proposed_description: ProposedDescription
    expected_last_modified: datetime
    confirm: bool


class DescriptionUpdateResult(BaseModel):
    change_id: int
    product_sf_id: str
    product_name: str | None
    previous_description: str | None
    description: str | None
    last_modified: datetime
    verified: bool


class DescriptionChangeItem(BaseModel):
    id: int
    product_sf_id: str
    product_name: str | None
    outcome: str
    previous_description: str | None
    proposed_description: str
    error_detail: str | None
    requested_by: str
    expected_last_modified: datetime
    salesforce_last_modified_after: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
