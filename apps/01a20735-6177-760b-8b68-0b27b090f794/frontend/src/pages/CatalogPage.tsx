import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { ChevronLeft, ChevronRight, Loader2, Package, Search } from 'lucide-react'
import client from '@/api/client'
import { CategoryTree } from '@/components/catalog/CategoryTree'
import { SectionGate } from '@/components/catalog/SectionGate'
import { SyncBar } from '@/components/catalog/SyncBar'
import { errorMessage } from '@/lib/notes'
import type { CatalogOverview, CategoryNode, ProductPage } from '@/lib/catalog'

const PAGE_SIZE = 25

function findCategory(nodes: CategoryNode[], id: string): CategoryNode | null {
  for (const n of nodes) {
    if (n.sf_id === id) return n
    const hit = findCategory(n.children, id)
    if (hit) return hit
  }
  return null
}

export default function CatalogPage() {
  const [params, setParams] = useSearchParams()
  const catalogId = params.get('catalog')
  const categoryId = params.get('category')
  const q = params.get('q') ?? ''
  const type = params.get('type') as 'bundle' | 'simple' | null
  const active = params.get('active')
  const page = Math.max(1, Number(params.get('page') ?? '1') || 1)
  const classificationId = params.get('classification')
  const requestSeq = useRef(0)

  const [overview, setOverview] = useState<CatalogOverview | null>(null)
  const [overviewError, setOverviewError] = useState<string | null>(null)
  const [products, setProducts] = useState<ProductPage | null>(null)
  const [listError, setListError] = useState<string | null>(null)
  const [loadingList, setLoadingList] = useState(true)
  const [search, setSearch] = useState(q)

  const loadOverview = useCallback(async () => {
    const { data, error } = await client.GET('/api/catalog/overview')
    if (!data) {
      setOverviewError(errorMessage(error, 'The catalog overview could not be loaded.'))
      return
    }
    setOverviewError(null)
    setOverview(data)
  }, [])

  const loadProducts = useCallback(async () => {
    const seq = ++requestSeq.current
    setLoadingList(true)
    const { data, error } = await client.GET('/api/catalog/products/', {
      params: {
        query: {
          q: q || undefined,
          catalog_id: catalogId || undefined,
          category_id: categoryId || undefined,
          classification_id: classificationId || undefined,
          product_type: type || undefined,
          is_active: active === null ? undefined : active === 'true',
          page,
          page_size: PAGE_SIZE,
        },
      },
    })
    // Ignore responses for filters the user has already moved away from.
    if (seq !== requestSeq.current) return
    setLoadingList(false)
    if (!data) {
      setListError(errorMessage(error, 'Products could not be loaded.'))
      return
    }
    setListError(null)
    setProducts(data)
  }, [q, catalogId, categoryId, classificationId, type, active, page])

  useEffect(() => {
    void loadOverview()
  }, [loadOverview])
  useEffect(() => {
    void loadProducts()
  }, [loadProducts])
  useEffect(() => setSearch(q), [q])

  const refreshAll = useCallback(() => {
    void loadOverview()
    void loadProducts()
  }, [loadOverview, loadProducts])

  function update(next: Record<string, string | null>, resetPage = true) {
    const p = new URLSearchParams(params)
    for (const [k, v] of Object.entries(next)) {
      if (v === null || v === '') p.delete(k)
      else p.set(k, v)
    }
    if (resetPage) p.delete('page')
    setParams(p)
  }

  const scopeTitle = useMemo(() => {
    if (!overview) return 'Products'
    const cat = overview.catalogs.find((c) => c.sf_id === catalogId)
    if (categoryId && cat) {
      const node = findCategory(cat.categories, categoryId)
      return node?.name ?? 'Category'
    }
    return cat?.name ?? 'All products'
  }, [overview, catalogId, categoryId])

  const scopeDescription = useMemo(() => {
    const cat = overview?.catalogs.find((c) => c.sf_id === catalogId)
    if (!cat) return null
    if (categoryId) return findCategory(cat.categories, categoryId)?.description ?? null
    return cat.description
  }, [overview, catalogId, categoryId])

  const classificationName = useMemo(
    () =>
      products?.items.find((i) => i.classification?.sf_id === classificationId)?.classification
        ?.name ?? null,
    [products, classificationId],
  )

  const t = overview?.totals
  return (
    <main className="mx-auto max-w-7xl px-5 py-6 sm:px-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">Revenue Cloud product catalog</h1>
          <p className="mt-1 text-sm text-ink-soft">
            Read from Salesforce, the source of truth.{' '}
            {t && (
              <>
                {t.catalogs} catalogs, {t.categories} categories, {t.products} products ({t.bundles}{' '}
                bundles), {t.price_books} price books.
              </>
            )}
          </p>
        </div>
        <SyncBar status={overview?.sync} onFinished={refreshAll} />
      </div>

      {overviewError && (
        <p
          role="alert"
          className="mt-4 rounded-xl border border-magenta bg-magenta-wash p-4 text-sm"
        >
          {overviewError}
        </p>
      )}

      {overview && !overview.sync.has_synced && (
        <div className="mt-6 rounded-2xl border-2 border-dashed border-cobalt/40 bg-sheet px-6 py-10 text-center">
          <Package className="mx-auto size-8 text-cobalt" />
          <p className="mt-2 font-bold">The catalog hasn’t been read from Salesforce yet</p>
          <p className="mt-1 text-sm text-ink-soft">
            Choose Sync changes to load catalogs, categories, products, attributes, bundles, and
            prices.
          </p>
        </div>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="lg:sticky lg:top-6 lg:max-h-[calc(100vh-3rem)] lg:self-start lg:overflow-y-auto">
          <div className="rounded-2xl border border-line bg-sheet p-3">
            <SectionGate sections={overview?.sections} name="catalog_navigation">
              {overview && (
                <CategoryTree
                  catalogs={overview.catalogs}
                  selection={{ catalogId, categoryId }}
                  onSelect={(s) => update({ catalog: s.catalogId, category: s.categoryId })}
                />
              )}
            </SectionGate>
          </div>
        </aside>

        <section aria-labelledby="scope-heading" className="min-w-0">
          <div className="rounded-2xl border border-line bg-sheet">
            <div className="border-b border-line p-4">
              <h2 id="scope-heading" className="text-lg font-bold">
                {scopeTitle}
                {products && (
                  <span className="ml-2 font-medium text-ink-soft">{products.total}</span>
                )}
              </h2>
              {scopeDescription && (
                <p className="mt-0.5 max-w-prose text-sm text-ink-soft">{scopeDescription}</p>
              )}
              <form
                className="mt-3 flex flex-wrap gap-2"
                onSubmit={(e) => {
                  e.preventDefault()
                  update({ q: search.trim() })
                }}
              >
                <label className="relative min-w-56 flex-1">
                  <span className="sr-only">Search products</span>
                  <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-ink-soft" />
                  <input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search name, product code, description, or Salesforce ID"
                    className="w-full rounded-lg border border-line bg-paper py-2 pr-3 pl-9 text-sm focus:border-cobalt focus:bg-sheet focus:outline-none"
                  />
                </label>
                <select
                  aria-label="Product type"
                  value={type ?? ''}
                  onChange={(e) => update({ type: e.target.value })}
                  className="rounded-lg border border-line bg-sheet px-3 py-2 text-sm"
                >
                  <option value="">All types</option>
                  <option value="bundle">Bundles</option>
                  <option value="simple">Simple products</option>
                </select>
                <select
                  aria-label="Status"
                  value={active ?? ''}
                  onChange={(e) => update({ active: e.target.value })}
                  className="rounded-lg border border-line bg-sheet px-3 py-2 text-sm"
                >
                  <option value="">Active and inactive</option>
                  <option value="true">Active only</option>
                  <option value="false">Inactive only</option>
                </select>
                <button
                  type="submit"
                  className="rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-white hover:bg-cobalt-deep focus-visible:outline-2 focus-visible:outline-cobalt"
                >
                  Search
                </button>
              </form>
            </div>

            <SectionGate sections={overview?.sections} name="products">
              {listError ? (
                <p role="alert" className="p-6 text-sm text-magenta-deep">
                  {listError}
                </p>
              ) : !products ? (
                <p className="flex items-center gap-2 p-6 text-sm text-ink-soft">
                  <Loader2 className="size-4 animate-spin" /> Loading products…
                </p>
              ) : products.items.length === 0 ? (
                <div className="px-6 py-12 text-center">
                  <p className="font-semibold">No products match</p>
                  <p className="mt-1 text-sm text-ink-soft">
                    {overview?.sync.has_synced
                      ? 'Try another search or choose a different catalog or category.'
                      : 'Run a sync to load products from Salesforce.'}
                  </p>
                </div>
              ) : (
                <div className={`overflow-x-auto ${loadingList ? 'opacity-60' : ''}`}>
                  <table className="w-full text-left text-sm">
                    <thead className="bg-paper text-ink-soft">
                      <tr>
                        <th className="px-4 py-2.5 font-semibold">Product</th>
                        <th className="px-4 py-2.5 font-semibold">Type</th>
                        <th className="px-4 py-2.5 font-semibold">Categories</th>
                        <th className="px-4 py-2.5 font-semibold">Classification</th>
                        <th className="px-4 py-2.5 font-semibold">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line">
                      {products.items.map((p) => (
                        <tr key={p.sf_id} className="align-top hover:bg-cobalt-wash/40">
                          <td className="max-w-md px-4 py-3">
                            <Link
                              to={`/catalog/products/${p.sf_id}`}
                              className="font-semibold text-ink hover:text-cobalt focus-visible:outline-2 focus-visible:outline-cobalt"
                            >
                              {p.name ?? p.sf_id}
                            </Link>
                            <span className="block text-xs text-ink-soft">
                              {p.product_code ?? 'No product code'}
                            </span>
                            {p.description ? (
                              <span className="mt-1 line-clamp-2 block text-xs text-ink-soft">
                                {p.description}
                              </span>
                            ) : (
                              <span className="mt-1 block text-xs text-ink-soft italic">
                                No description
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            {p.type === 'Bundle' ? (
                              <span className="rounded-full bg-cobalt-wash px-2 py-0.5 text-xs font-semibold text-cobalt-deep">
                                Bundle
                              </span>
                            ) : (
                              <span className="text-ink-soft">{p.type ?? 'Simple'}</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-ink-soft">
                            {p.category_names.join(', ') || '—'}
                          </td>
                          <td className="px-4 py-3 text-ink-soft">
                            {p.classification?.name ?? '—'}
                          </td>
                          <td className="px-4 py-3">
                            {p.is_active ? (
                              <span className="font-semibold text-teal-deep">Active</span>
                            ) : (
                              <span className="text-ink-soft">Inactive</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {products && products.total > 0 && (
                <div className="flex items-center justify-between border-t border-line px-4 py-3 text-sm">
                  <span className="text-ink-soft">
                    {(products.page - 1) * products.page_size + 1}–
                    {Math.min(products.page * products.page_size, products.total)} of{' '}
                    {products.total}
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      disabled={products.page <= 1}
                      onClick={() => update({ page: String(products.page - 1) }, false)}
                      className="inline-flex items-center gap-1 rounded-lg border border-line px-2.5 py-1.5 font-semibold disabled:opacity-40"
                    >
                      <ChevronLeft className="size-4" /> Previous
                    </button>
                    <span className="tabular-nums">
                      Page {products.page} of {products.total_pages}
                    </span>
                    <button
                      type="button"
                      disabled={products.page >= products.total_pages}
                      onClick={() => update({ page: String(products.page + 1) }, false)}
                      className="inline-flex items-center gap-1 rounded-lg border border-line px-2.5 py-1.5 font-semibold disabled:opacity-40"
                    >
                      Next <ChevronRight className="size-4" />
                    </button>
                  </div>
                </div>
              )}
            </SectionGate>
          </div>
        </section>
      </div>
    </main>
  )
}
