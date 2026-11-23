import type { components } from '@/api/schema'

type S = components['schemas']
export type CatalogOverview = S['CatalogOverview']
export type CatalogSummary = S['CatalogSummary']
export type CategoryNode = S['CategoryNode']
export type CoverageItem = S['CoverageItem']
export type SectionAvailability = S['SectionAvailability']
export type ProductPage = S['ProductPage']
export type ProductListItem = S['ProductListItem']
export type ProductDetail = S['ProductDetail']
export type ProductAttributeItem = S['ProductAttributeItem']
export type BundleComponentItem = S['BundleComponentItem']
export type AttributeLibrary = S['AttributeLibrary']
export type LiveDescription = S['LiveDescription']
export type DescriptionPreview = S['DescriptionPreview']
export type DescriptionChangeItem = S['DescriptionChangeItem']
export type SyncStatus = S['CatalogSyncStatus']
export type CoverageStatus = CoverageItem['status']

export const STATUS_LABEL: Record<CoverageStatus, string> = {
  synced: 'Synced',
  empty: 'Readable, no records',
  not_mapped: 'Readable, not shown yet',
  not_available: 'Not in this org',
  blocked: 'Blocked',
  error: 'Error',
  never_synced: 'Not synced yet',
}

export const SECTION_LABEL: Record<string, string> = {
  catalog_navigation: 'Catalogs and categories',
  products: 'Products',
  classification: 'Product classifications',
  attributes: 'Attribute definitions and groups',
  product_attributes: 'Product attribute assignments',
  bundles: 'Bundle structure',
  selling_models: 'Selling models',
  price_books: 'Price books',
}

export function section(
  sections: SectionAvailability[] | undefined,
  name: string,
): SectionAvailability | undefined {
  return sections?.find((s) => s.section === name)
}

const dateFmt = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' })
const dayFmt = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' })

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : dateFmt.format(d)
}

export function formatDay(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : dayFmt.format(d)
}

const numFmt = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 })
export function formatNumber(n: number | null | undefined): string {
  return n === null || n === undefined ? '—' : numFmt.format(n)
}

export function yesNo(v: boolean | null | undefined): string {
  return v === null || v === undefined ? '—' : v ? 'Yes' : 'No'
}
