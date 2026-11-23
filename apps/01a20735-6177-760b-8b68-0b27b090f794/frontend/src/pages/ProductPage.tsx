import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { Link, useParams } from 'react-router'
import { ArrowLeft, ExternalLink, Loader2 } from 'lucide-react'
import client from '@/api/client'
import { DescriptionEditor } from '@/components/catalog/DescriptionEditor'
import { SectionGate } from '@/components/catalog/SectionGate'
import { errorMessage } from '@/lib/notes'
import {
  formatDateTime,
  formatDay,
  formatNumber,
  yesNo,
  type BundleComponentItem,
  type DescriptionChangeItem,
  type ProductDetail,
} from '@/lib/catalog'

function Block({ title, children, count }: { title: string; children: ReactNode; count?: number }) {
  return (
    <section className="rounded-2xl border border-line bg-sheet p-5">
      <h2 className="text-lg font-bold">
        {title}
        {count !== undefined && <span className="ml-2 font-medium text-ink-soft">{count}</span>}
      </h2>
      <div className="mt-3">{children}</div>
    </section>
  )
}

function Empty({ children }: { children: ReactNode }) {
  return <p className="text-sm text-ink-soft">{children}</p>
}

function Fact({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-ink-soft">{label}</dt>
      <dd className="text-sm font-semibold break-words">{value ?? '—'}</dd>
    </div>
  )
}

function ComponentRow({ c }: { c: BundleComponentItem }) {
  const target = c.child_product ?? c.child_classification
  return (
    <tr className="align-top">
      <td className="py-2 pr-4">
        {c.child_product ? (
          <Link
            to={`/catalog/products/${c.child_product.sf_id}`}
            className="font-semibold hover:text-cobalt"
          >
            {c.child_product.name ?? c.child_product.sf_id}
          </Link>
        ) : (
          <span className="font-semibold">{target?.name ?? target?.sf_id ?? '—'}</span>
        )}
        {c.child_classification && !c.child_product && (
          <span className="block text-xs text-ink-soft">Any product of this classification</span>
        )}
      </td>
      <td className="py-2 pr-4 tabular-nums">
        {formatNumber(c.quantity)}
        {(c.min_quantity !== null || c.max_quantity !== null) && (
          <span className="block text-xs text-ink-soft">
            {formatNumber(c.min_quantity)} to {formatNumber(c.max_quantity)}
          </span>
        )}
      </td>
      <td className="py-2 pr-4">
        {c.is_required ? (
          <span className="font-semibold text-cobalt-deep">Required</span>
        ) : (
          'Optional'
        )}
      </td>
      <td className="py-2 pr-4">{yesNo(c.is_default)}</td>
      <td className="py-2">{yesNo(c.price_included_in_bundle)}</td>
    </tr>
  )
}

function ComponentTable({ components }: { components: BundleComponentItem[] }) {
  if (components.length === 0) return <Empty>No components in this group.</Empty>
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="text-xs text-ink-soft">
          <tr>
            <th className="pr-4 pb-1 font-semibold">Component</th>
            <th className="pr-4 pb-1 font-semibold">Quantity</th>
            <th className="pr-4 pb-1 font-semibold">Required</th>
            <th className="pr-4 pb-1 font-semibold">Selected by default</th>
            <th className="pb-1 font-semibold">Included in bundle price</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {components.map((c) => (
            <ComponentRow key={c.sf_id} c={c} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function ProductPage() {
  const { productId = '' } = useParams()
  const [product, setProduct] = useState<ProductDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [history, setHistory] = useState<DescriptionChangeItem[]>([])

  const load = useCallback(async () => {
    setProduct((prev) => (prev && prev.sf_id !== productId ? null : prev))
    const { data, error: err } = await client.GET('/api/catalog/products/{product_id}', {
      params: { path: { product_id: productId } },
    })
    if (!data) {
      setError(errorMessage(err, 'This product could not be loaded.'))
      return
    }
    setError(null)
    setProduct(data)
    const h = await client.GET('/api/catalog/products/{product_id}/description/history', {
      params: { path: { product_id: productId } },
    })
    setHistory(h.data ?? [])
  }, [productId])

  useEffect(() => {
    void load()
  }, [load])

  if (error)
    return (
      <main className="mx-auto max-w-5xl px-5 py-8 sm:px-8">
        <Link
          to="/catalog"
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-cobalt"
        >
          <ArrowLeft className="size-4" /> Back to catalog
        </Link>
        <p role="alert" className="mt-4 rounded-xl border border-magenta bg-magenta-wash p-5">
          {error}
        </p>
      </main>
    )
  if (!product)
    return (
      <main className="flex items-center justify-center gap-2 py-20 text-ink-soft">
        <Loader2 className="size-4 animate-spin" /> Loading product…
      </main>
    )

  const p = product
  const s = p.sections
  return (
    <main className="mx-auto max-w-5xl space-y-5 px-5 py-6 sm:px-8">
      <Link
        to="/catalog"
        className="inline-flex items-center gap-1.5 text-sm font-semibold text-cobalt"
      >
        <ArrowLeft className="size-4" /> Back to catalog
      </Link>

      <header className="rounded-2xl border border-line bg-sheet p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight">{p.name ?? p.sf_id}</h1>
            <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-ink-soft">
              <span>{p.product_code ?? 'No product code'}</span>
              {p.type === 'Bundle' && (
                <span className="rounded-full bg-cobalt-wash px-2 py-0.5 text-xs font-semibold text-cobalt-deep">
                  Bundle
                </span>
              )}
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-semibold ${p.is_active ? 'bg-teal-wash text-teal-deep' : 'bg-paper text-ink-soft ring-1 ring-line'}`}
              >
                {p.is_active ? 'Active' : 'Inactive'}
              </span>
              {p.is_archived && (
                <span className="rounded-full bg-paper px-2 py-0.5 text-xs ring-1 ring-line">
                  Archived
                </span>
              )}
            </p>
          </div>
          {p.salesforce_url && (
            <a
              href={p.salesforce_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 text-sm font-semibold text-cobalt hover:underline"
            >
              Open in Salesforce <ExternalLink className="size-4" />
            </a>
          )}
        </div>
        <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-3 sm:grid-cols-4">
          <Fact
            label="Salesforce ID"
            value={<span className="font-mono text-xs">{p.sf_id}</span>}
          />
          <Fact label="Family" value={p.family} />
          <Fact
            label="Classification"
            value={
              p.classification ? (
                <Link
                  to={`/catalog?classification=${p.classification.sf_id}`}
                  className="text-cobalt hover:underline"
                >
                  {p.classification.name ?? p.classification.sf_id}
                </Link>
              ) : (
                '—'
              )
            }
          />
          <Fact label="Configure during sale" value={p.configure_during_sale} />
          <Fact label="SKU" value={p.stock_keeping_unit} />
          <Fact label="Unit of measure" value={p.quantity_unit_of_measure} />
          <Fact label="Assetizable" value={yesNo(p.is_assetizable)} />
          <Fact
            label="Sold only with other products"
            value={yesNo(p.is_sold_only_with_other_products)}
          />
          <Fact label="Available from" value={formatDay(p.availability_date)} />
          <Fact label="Discontinued" value={formatDay(p.discontinued_date)} />
          <Fact label="Last modified in Salesforce" value={formatDateTime(p.last_modified)} />
          <Fact label="Synced" value={formatDateTime(p.synced_at)} />
        </dl>
      </header>

      <section className="rounded-2xl border border-line bg-sheet p-5">
        <DescriptionEditor
          productId={p.sf_id}
          cachedDescription={p.description}
          onSaved={() => void load()}
        />
        {history.length > 0 && (
          <details className="mt-4 border-t border-line pt-3">
            <summary className="cursor-pointer text-sm font-semibold text-ink-soft">
              Description change history ({history.length})
            </summary>
            <ul className="mt-2 space-y-2 text-sm">
              {history.map((h) => (
                <li key={h.id} className="rounded-lg bg-paper px-3 py-2">
                  <span
                    className={`font-semibold ${h.outcome === 'applied' ? 'text-teal-deep' : 'text-magenta-deep'}`}
                  >
                    {h.outcome === 'applied'
                      ? 'Saved'
                      : h.outcome === 'conflict'
                        ? 'Blocked by a newer change'
                        : h.outcome === 'failed'
                          ? 'Rejected by Salesforce'
                          : 'Saved, not verified'}
                  </span>{' '}
                  by {h.requested_by} on {formatDateTime(h.created_at)}
                  {h.error_detail && (
                    <span className="block text-xs text-ink-soft">{h.error_detail}</span>
                  )}
                </li>
              ))}
            </ul>
          </details>
        )}
      </section>

      <Block title="Catalogs and categories" count={p.memberships.length}>
        <SectionGate sections={s} name="catalog_navigation">
          {p.memberships.length === 0 ? (
            <Empty>This product isn’t assigned to any catalog category.</Empty>
          ) : (
            <ul className="flex flex-wrap gap-2">
              {p.memberships.map((m) => (
                <li key={m.sf_id}>
                  <Link
                    to={`/catalog?catalog=${m.catalog?.sf_id ?? ''}&category=${m.category?.sf_id ?? ''}`}
                    className="inline-block rounded-lg border border-line bg-paper px-3 py-1.5 text-sm hover:border-cobalt"
                  >
                    <span className="text-ink-soft">{m.catalog?.name ?? 'Catalog'}:</span>{' '}
                    <span className="font-semibold">
                      {m.category_path.join(' / ') || m.category?.name}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </SectionGate>
      </Block>

      <Block title="Attributes" count={p.attributes.length}>
        <SectionGate sections={s} name="product_attributes">
          {p.attributes.length === 0 ? (
            <Empty>
              No attributes are assigned to this product
              {p.classification ? ' or its classification' : ''}.
            </Empty>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs text-ink-soft">
                  <tr>
                    <th className="pr-4 pb-1 font-semibold">Attribute</th>
                    <th className="pr-4 pb-1 font-semibold">Group</th>
                    <th className="pr-4 pb-1 font-semibold">Type</th>
                    <th className="pr-4 pb-1 font-semibold">Default</th>
                    <th className="pr-4 pb-1 font-semibold">Values</th>
                    <th className="pb-1 font-semibold">Rules</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {p.attributes.map((a) => (
                    <tr key={a.sf_id} className="align-top">
                      <td className="py-2 pr-4">
                        <span className="font-semibold">{a.name ?? a.definition?.name}</span>
                        <span className="block text-xs text-ink-soft">
                          {a.source === 'product' ? 'Set on product' : 'From classification'}
                        </span>
                      </td>
                      <td className="py-2 pr-4">{a.category?.name ?? '—'}</td>
                      <td className="py-2 pr-4">{a.data_type ?? '—'}</td>
                      <td className="py-2 pr-4">{a.default_value ?? '—'}</td>
                      <td className="py-2 pr-4">
                        {a.picklist_values.length > 0 ? (
                          <span className="flex flex-wrap gap-1">
                            {a.picklist_values.map((v) => (
                              <span
                                key={v.sf_id}
                                className={`rounded px-1.5 py-0.5 text-xs ${v.is_default ? 'bg-cobalt text-white' : 'bg-cobalt-wash text-cobalt-deep'}`}
                              >
                                {v.label}
                              </span>
                            ))}
                          </span>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="py-2 text-xs text-ink-soft">
                        {[
                          a.is_required && 'Required',
                          a.is_read_only && 'Read only',
                          a.is_hidden && 'Hidden',
                          a.is_price_impacting && 'Affects price',
                          a.status && a.status !== 'Active' && a.status,
                        ]
                          .filter(Boolean)
                          .join(', ') || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionGate>
      </Block>

      <Block title="Bundle structure">
        <SectionGate sections={s} name="bundles">
          {!p.bundle ? (
            <Empty>
              {p.type === 'Bundle'
                ? 'This bundle has no component groups or components yet.'
                : 'This product is not a bundle.'}
            </Empty>
          ) : (
            <div className="space-y-4">
              {p.bundle.groups.map((g) => (
                <div key={g.sf_id} className="rounded-xl border border-line p-4">
                  <p className="font-bold">
                    {g.name ?? 'Group'}
                    {(g.min_components !== null || g.max_components !== null) && (
                      <span className="ml-2 text-sm font-medium text-ink-soft">
                        choose {g.min_components ?? 0} to {g.max_components ?? 'any'}
                      </span>
                    )}
                  </p>
                  {g.description && <p className="text-sm text-ink-soft">{g.description}</p>}
                  <div className="mt-2">
                    <ComponentTable components={g.components} />
                  </div>
                </div>
              ))}
              {p.bundle.ungrouped_components.length > 0 && (
                <div className="rounded-xl border border-line p-4">
                  <p className="font-bold">Components outside a group</p>
                  <div className="mt-2">
                    <ComponentTable components={p.bundle.ungrouped_components} />
                  </div>
                </div>
              )}
            </div>
          )}
          {p.used_in_bundles.length > 0 && (
            <p className="mt-3 text-sm">
              <span className="text-ink-soft">Included in bundles: </span>
              {p.used_in_bundles.map((b, i) => (
                <span key={b.sf_id}>
                  {i > 0 && ', '}
                  <Link
                    to={`/catalog/products/${b.sf_id}`}
                    className="font-semibold text-cobalt hover:underline"
                  >
                    {b.name ?? b.sf_id}
                  </Link>
                </span>
              ))}
            </p>
          )}
        </SectionGate>
      </Block>

      <div className="grid gap-5 md:grid-cols-2">
        <Block title="Selling models" count={p.selling_models.length}>
          <SectionGate sections={s} name="selling_models">
            {p.selling_models.length === 0 ? (
              <Empty>No selling models are assigned.</Empty>
            ) : (
              <ul className="space-y-2 text-sm">
                {p.selling_models.map((m) => (
                  <li key={m.sf_id} className="flex flex-wrap items-baseline justify-between gap-2">
                    <span className="font-semibold">
                      {m.selling_model?.name ?? '—'}
                      {m.is_default && (
                        <span className="ml-2 rounded bg-cobalt-wash px-1.5 text-xs text-cobalt-deep">
                          Default
                        </span>
                      )}
                    </span>
                    <span className="text-ink-soft">
                      {m.selling_model_type}
                      {m.pricing_term ? `, ${m.pricing_term} ${m.pricing_term_unit ?? ''}` : ''}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </SectionGate>
        </Block>
        <Block title="Prices" count={p.price_entries.length}>
          <SectionGate sections={s} name="price_books">
            {p.price_entries.length === 0 ? (
              <Empty>No price book entries for this product.</Empty>
            ) : (
              <ul className="space-y-2 text-sm">
                {p.price_entries.map((e) => (
                  <li key={e.sf_id} className="flex flex-wrap items-baseline justify-between gap-2">
                    <span>
                      <span className="font-semibold">{e.price_book?.name ?? '—'}</span>
                      {e.selling_model && (
                        <span className="text-ink-soft">, {e.selling_model.name}</span>
                      )}
                      {!e.is_active && <span className="ml-2 text-xs text-ink-soft">inactive</span>}
                    </span>
                    <span className="font-bold tabular-nums">{formatNumber(e.unit_price)}</span>
                  </li>
                ))}
              </ul>
            )}
            <p className="mt-2 text-xs text-ink-soft">Amounts in the org’s single currency.</p>
          </SectionGate>
        </Block>
      </div>
    </main>
  )
}
