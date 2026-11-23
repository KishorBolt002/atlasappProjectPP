"""Metadata-verified Revenue Cloud catalog objects and the fields the app caches.

Field lists come from describe calls against the connected org (see
backend/salesforce-schema.yaml). At sync time each list is intersected with a
fresh describe, so a field hidden by field-level security is reported as
missing instead of breaking the query or reading as empty.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CatalogObject:
    api_name: str
    label: str
    section: str
    fields: tuple[str, ...] = field(default_factory=tuple)
    name_field: str | None = "Name"
    code_field: str | None = None
    mapped: bool = True


SECTION_CATALOG = "catalogs"
SECTION_PRODUCTS = "products"
SECTION_ATTRIBUTES = "attributes"
SECTION_BUNDLES = "bundles"
SECTION_PRICING = "pricing"
SECTION_OTHER = "other"

MAPPED_OBJECTS: tuple[CatalogObject, ...] = (
    CatalogObject(
        "ProductCatalog",
        "Catalog",
        SECTION_CATALOG,
        (
            "Name",
            "Code",
            "Description",
            "CatalogType",
            "EffectiveStartDate",
            "EffectiveEndDate",
            "NumberOfCategories",
        ),
        code_field="Code",
    ),
    CatalogObject(
        "ProductCategory",
        "Category",
        SECTION_CATALOG,
        (
            "Name",
            "Code",
            "Description",
            "CatalogId",
            "ParentCategoryId",
            "SortOrder",
            "IsNavigational",
            "NumberOfProducts",
        ),
        code_field="Code",
    ),
    CatalogObject(
        "ProductCategoryProduct",
        "Product Category Product",
        SECTION_CATALOG,
        ("Name", "ProductCategoryId", "ProductId", "CatalogId"),
    ),
    CatalogObject(
        "Product2",
        "Product",
        SECTION_PRODUCTS,
        (
            "Name",
            "ProductCode",
            "Description",
            "IsActive",
            "Family",
            "Type",
            "ConfigureDuringSale",
            "BasedOnId",
            "StockKeepingUnit",
            "QuantityUnitOfMeasure",
            "IsAssetizable",
            "IsSoldOnlyWithOtherProds",
            "AvailabilityDate",
            "DiscontinuedDate",
            "EndOfLifeDate",
            "HelpText",
            "DisplayUrl",
            "SpecificationType",
            "IsArchived",
            "DecompositionScope",
            "UsageModelType",
            "CanRamp",
            "ExternalId",
            "SourceProductId",
        ),
        code_field="ProductCode",
    ),
    CatalogObject(
        "ProductClassification",
        "Product Classification",
        SECTION_ATTRIBUTES,
        ("Name", "Code", "Status", "ParentProductClassificationId"),
        code_field="Code",
    ),
    CatalogObject(
        "ProductClassificationAttr",
        "Product Classification Attribute",
        SECTION_ATTRIBUTES,
        (
            "Name",
            "ProductClassificationId",
            "AttributeDefinitionId",
            "AttributeCategoryId",
            "AttributeNameOverride",
            "DefaultValue",
            "IsRequired",
            "IsHidden",
            "IsReadOnly",
            "IsPriceImpacting",
            "Status",
            "Sequence",
            "DisplayType",
            "ExcludedPicklistValues",
            "MinimumValue",
            "MaximumValue",
            "StepValue",
            "HelpText",
            "Description",
        ),
    ),
    CatalogObject(
        "AttributeDefinition",
        "Attribute Definition",
        SECTION_ATTRIBUTES,
        (
            "Name",
            "Label",
            "Code",
            "DeveloperName",
            "Description",
            "DataType",
            "IsActive",
            "IsRequired",
            "DefaultValue",
            "PicklistId",
            "DefaultHelpText",
            "UnitOfMeasureId",
        ),
        code_field="Code",
    ),
    CatalogObject(
        "AttributeCategory",
        "Attribute Category",
        SECTION_ATTRIBUTES,
        ("Name", "Code", "Description"),
        code_field="Code",
    ),
    CatalogObject(
        "AttributeCategoryAttribute",
        "Attribute Category Attribute",
        SECTION_ATTRIBUTES,
        ("Name", "AttributeCategoryId", "AttributeDefinitionId"),
    ),
    CatalogObject(
        "AttributePicklist",
        "Attribute Picklist",
        SECTION_ATTRIBUTES,
        ("Name", "Code", "Description", "Status", "DataType"),
        code_field="Code",
    ),
    CatalogObject(
        "AttributePicklistValue",
        "Attribute Picklist Value",
        SECTION_ATTRIBUTES,
        (
            "Name",
            "PicklistId",
            "Code",
            "DisplayValue",
            "Value",
            "IsDefault",
            "Sequence",
            "Status",
            "Abbreviation",
        ),
        code_field="Code",
    ),
    CatalogObject(
        "ProductAttributeDefinition",
        "Product Attribute Definition",
        SECTION_ATTRIBUTES,
        (
            "Name",
            "Product2Id",
            "AttributeDefinitionId",
            "AttributeCategoryId",
            "ProductClassificationAttributeId",
            "AttributeNameOverride",
            "DefaultValue",
            "IsRequired",
            "IsHidden",
            "IsReadOnly",
            "IsPriceImpacting",
            "Status",
            "Sequence",
            "DisplayType",
            "ExcludedPicklistValues",
            "MinimumValue",
            "MaximumValue",
            "HelpText",
            "Description",
            "OverrideContextId",
        ),
    ),
    CatalogObject(
        "ProductComponentGroup",
        "Product Component Group",
        SECTION_BUNDLES,
        (
            "Name",
            "Code",
            "ParentProductId",
            "ParentGroupId",
            "Description",
            "MinBundleComponents",
            "MaxBundleComponents",
            "Sequence",
        ),
        code_field="Code",
    ),
    CatalogObject(
        "ProductRelatedComponent",
        "Product Related Component",
        SECTION_BUNDLES,
        (
            "Name",
            "ParentProductId",
            "ChildProductId",
            "ProductComponentGroupId",
            "ProductRelationshipTypeId",
            "Quantity",
            "MinQuantity",
            "MaxQuantity",
            "IsComponentRequired",
            "IsDefaultComponent",
            "IsQuantityEditable",
            "DoesBundlePriceIncludeChild",
            "Sequence",
            "ParentSellingModelId",
            "ChildSellingModelId",
            "ChildProductClassificationId",
            "QuantityScaleMethod",
        ),
    ),
    CatalogObject(
        "ProductRelationshipType",
        "Product Relationship Type",
        SECTION_BUNDLES,
        ("Name", "MainProductRoleCat", "AssociatedProductRoleCat"),
    ),
    CatalogObject(
        "ProductSellingModel",
        "Product Selling Model",
        SECTION_PRICING,
        ("Name", "SellingModelType", "PricingTerm", "PricingTermUnit", "Status"),
    ),
    CatalogObject(
        "ProductSellingModelOption",
        "Product Selling Model Option",
        SECTION_PRICING,
        ("Name", "ProductSellingModelId", "Product2Id", "IsDefault"),
    ),
    CatalogObject(
        "Pricebook2",
        "Price Book",
        SECTION_PRICING,
        (
            "Name",
            "Description",
            "IsActive",
            "IsStandard",
            "IsArchived",
            "ValidFrom",
            "ValidTo",
        ),
    ),
    CatalogObject(
        "PricebookEntry",
        "Price Book Entry",
        SECTION_PRICING,
        (
            "Name",
            "Pricebook2Id",
            "Product2Id",
            "ProductSellingModelId",
            "UnitPrice",
            "IsActive",
            "UseStandardPrice",
            "IsArchived",
        ),
    ),
)

# Readable catalog structures that are counted for coverage but not cached or
# shown in this version of the app.
COVERAGE_ONLY_OBJECTS: tuple[CatalogObject, ...] = tuple(
    CatalogObject(api, label, SECTION_OTHER, mapped=False)
    for api, label in (
        ("ProductQualification", "Product Qualification"),
        ("ProductDisqualification", "Product Disqualification"),
        ("ProductCategoryQualification", "Product Category Qualification"),
        ("ProductCategoryDisqual", "Product Category Disqualification"),
        ("ProductRampSegment", "Product Ramp Segment"),
        ("ProductUsageGrant", "Product Usage Grant"),
        ("PriceBookEntryDerivedPrice", "Price Book Entry Derived Price"),
        ("ProductConfigurationRule", "Product Configuration Rule"),
        ("ProductComponentGrpOverride", "Product Component Group Override"),
        ("ProductRelComponentOverride", "Product Related Component Override"),
        ("ProductSpecificationType", "Product Specification Type"),
        ("ProductSpecificationRecType", "Product Specification Record Type"),
    )
)

ALL_OBJECTS: tuple[CatalogObject, ...] = MAPPED_OBJECTS + COVERAGE_ONLY_OBJECTS
OBJECTS_BY_NAME = {o.api_name: o for o in ALL_OBJECTS}

# Which coverage rows each UI section depends on; a section is shown as
# unavailable when any of these is not readable.
SECTION_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "catalog_navigation": (
        "ProductCatalog",
        "ProductCategory",
        "ProductCategoryProduct",
    ),
    "products": ("Product2",),
    "classification": ("ProductClassification", "ProductClassificationAttr"),
    "attributes": (
        "AttributeDefinition",
        "AttributeCategory",
        "AttributeCategoryAttribute",
        "AttributePicklist",
        "AttributePicklistValue",
    ),
    "product_attributes": ("ProductAttributeDefinition", "AttributeDefinition"),
    "bundles": ("ProductComponentGroup", "ProductRelatedComponent"),
    "selling_models": ("ProductSellingModel", "ProductSellingModelOption"),
    "price_books": ("Pricebook2", "PricebookEntry"),
}
