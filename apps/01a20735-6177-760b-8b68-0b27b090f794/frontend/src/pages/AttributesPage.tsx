import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router'
import { Loader2, Search } from 'lucide-react'
import client from '@/api/client'
import { SectionGate } from '@/components/catalog/SectionGate'
import { errorMessage } from '@/lib/notes'
import type { AttributeLibrary } from '@/lib/catalog'

type Tab = 'definitions' | 'groups' | 'classifications' | 'picklists'
const TABS: { id: Tab; label: string }[] = [
  { id: 'definitions', label: 'Attribute definitions' },
  { id: 'groups', label: 'Attribute groups' },
  { id: 'classifications', label: 'Classifications' },
  { id: 'picklists', label: 'Picklists' },
]

export default function AttributesPage() {
  const [lib, setLib] = useState<AttributeLibrary | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<Tab>('definitions')
  const [q, setQ] = useState('')

  useEffect(() => {
    client.GET('/api/catalog/attributes').then(({ data, error: err }) => {
      if (data) setLib(data)
      else setError(errorMessage(err, 'The attribute library could not be loaded.'))
    })
  }, [])

  const needle = q.trim().toLowerCase()
  const match = (...vals: (string | null | undefined)[]) =>
    !needle || vals.some((v) => v?.toLowerCase().includes(needle))

  const counts = useMemo(
    () =>
      lib
        ? {
            definitions: lib.definitions.length,
            groups: lib.categories.length,
            classifications: lib.classifications.length,
            picklists: lib.picklists.length,
          }
        : null,
    [lib],
  )

  return (
    <main className="mx-auto max-w-7xl px-5 py-6 sm:px-8">
      <h1 className="text-2xl font-extrabold tracking-tight">Attributes and classifications</h1>
      <p className="mt-1 text-sm text-ink-soft">
        How Revenue Cloud describes products: attribute definitions, the groups they belong to, the
        classifications that bundle them, and their picklist values.{' '}
        <Link to="/catalog/coverage" className="font-semibold text-cobalt">
          Coverage and sync
        </Link>
      </p>
      {error && (
        <p
          role="alert"
          className="mt-4 rounded-xl border border-magenta bg-magenta-wash p-4 text-sm"
        >
          {error}
        </p>
      )}
      {!lib && !error && (
        <p className="mt-6 flex items-center gap-2 text-ink-soft">
          <Loader2 className="size-4 animate-spin" /> Loading…
        </p>
      )}
      {lib && (
        <>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <div
              role="tablist"
              className="flex flex-wrap gap-1 rounded-xl bg-sheet p-1 ring-1 ring-line"
            >
              {TABS.map((t) => (
                <button
                  key={t.id}
                  role="tab"
                  aria-selected={tab === t.id}
                  onClick={() => setTab(t.id)}
                  className={`rounded-lg px-3 py-1.5 text-sm font-semibold ${tab === t.id ? 'bg-cobalt text-white' : 'text-ink-soft hover:bg-cobalt-wash'}`}
                >
                  {t.label} <span className="tabular-nums opacity-80">{counts?.[t.id]}</span>
                </button>
              ))}
            </div>
            <label className="relative min-w-56 flex-1">
              <span className="sr-only">Filter</span>
              <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-ink-soft" />
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Filter by name or code"
                className="w-full rounded-lg border border-line bg-sheet py-2 pr-3 pl-9 text-sm focus:border-cobalt focus:outline-none"
              />
            </label>
          </div>

          <div className="mt-4 overflow-hidden rounded-2xl border border-line bg-sheet">
            {tab === 'definitions' && (
              <SectionGate sections={lib.sections} name="attributes">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-paper text-ink-soft">
                      <tr>
                        <th className="px-4 py-2.5 font-semibold">Attribute</th>
                        <th className="px-4 py-2.5 font-semibold">Data type</th>
                        <th className="px-4 py-2.5 font-semibold">Groups</th>
                        <th className="px-4 py-2.5 font-semibold">Values</th>
                        <th className="px-4 py-2.5 font-semibold">Used by</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line">
                      {lib.definitions
                        .filter((d) => match(d.name, d.label, d.code, d.developer_name))
                        .map((d) => (
                          <tr key={d.sf_id} className="align-top">
                            <td className="px-4 py-3">
                              <span className="font-semibold">{d.label || d.name}</span>
                              <span className="block text-xs text-ink-soft">
                                {[
                                  d.code,
                                  d.is_active === false ? 'Inactive' : null,
                                  d.is_required ? 'Required' : null,
                                ]
                                  .filter(Boolean)
                                  .join(', ') || d.developer_name}
                              </span>
                              {d.description && (
                                <span className="mt-1 block text-xs text-ink-soft">
                                  {d.description}
                                </span>
                              )}
                            </td>
                            <td className="px-4 py-3">{d.data_type ?? '—'}</td>
                            <td className="px-4 py-3">
                              {d.categories.map((c) => c.name).join(', ') || '—'}
                            </td>
                            <td className="px-4 py-3">
                              {d.picklist_values.length > 0 ? (
                                <span className="flex flex-wrap gap-1">
                                  {d.picklist_values.map((v) => (
                                    <span
                                      key={v.sf_id}
                                      className="rounded bg-cobalt-wash px-1.5 py-0.5 text-xs text-cobalt-deep"
                                    >
                                      {v.label}
                                    </span>
                                  ))}
                                </span>
                              ) : (
                                (d.default_value ?? '—')
                              )}
                            </td>
                            <td className="px-4 py-3 text-ink-soft">
                              {d.classification_count} classifications, {d.product_count} products
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </SectionGate>
            )}

            {tab === 'groups' && (
              <SectionGate sections={lib.sections} name="attributes">
                <ul className="divide-y divide-line">
                  {lib.categories
                    .filter((c) => match(c.name, c.code))
                    .map((c) => (
                      <li key={c.sf_id} className="px-4 py-3">
                        <p className="font-semibold">
                          {c.name}{' '}
                          {c.code && (
                            <span className="text-xs font-normal text-ink-soft">{c.code}</span>
                          )}
                        </p>
                        {c.description && <p className="text-sm text-ink-soft">{c.description}</p>}
                        <p className="mt-1 text-sm">
                          {c.attributes.length > 0 ? (
                            c.attributes.map((a) => a.name).join(', ')
                          ) : (
                            <span className="text-ink-soft">No attributes linked</span>
                          )}
                        </p>
                      </li>
                    ))}
                </ul>
              </SectionGate>
            )}

            {tab === 'classifications' && (
              <SectionGate sections={lib.sections} name="classification">
                <ul className="divide-y divide-line">
                  {lib.classifications
                    .filter((c) => match(c.name, c.code))
                    .map((c) => (
                      <li key={c.sf_id} className="px-4 py-3">
                        <div className="flex flex-wrap items-baseline justify-between gap-2">
                          <p className="font-semibold">
                            {c.name}{' '}
                            {c.code && (
                              <span className="text-xs font-normal text-ink-soft">{c.code}</span>
                            )}
                            {c.parent && (
                              <span className="ml-2 text-xs font-normal text-ink-soft">
                                inherits from {c.parent.name}
                              </span>
                            )}
                          </p>
                          <span className="text-sm text-ink-soft">
                            {c.status},{' '}
                            {c.product_count > 0 ? (
                              <Link
                                to={`/catalog?classification=${c.sf_id}`}
                                className="font-semibold text-cobalt hover:underline"
                              >
                                {c.product_count} products
                              </Link>
                            ) : (
                              '0 products'
                            )}
                          </span>
                        </div>
                        {c.attributes.length > 0 ? (
                          <ul className="mt-1 flex flex-wrap gap-1.5">
                            {c.attributes.map((a) => (
                              <li
                                key={a.sf_id}
                                className="rounded-lg bg-paper px-2 py-1 text-xs ring-1 ring-line"
                              >
                                <span className="font-semibold">{a.name}</span>
                                {a.category && (
                                  <span className="text-ink-soft"> in {a.category.name}</span>
                                )}
                                {a.is_required && (
                                  <span className="text-cobalt-deep">, required</span>
                                )}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="mt-1 text-sm text-ink-soft">No attributes</p>
                        )}
                      </li>
                    ))}
                </ul>
              </SectionGate>
            )}

            {tab === 'picklists' && (
              <SectionGate sections={lib.sections} name="attributes">
                <ul className="divide-y divide-line">
                  {lib.picklists
                    .filter((p) => match(p.name, p.code))
                    .map((p) => (
                      <li key={p.sf_id} className="px-4 py-3">
                        <p className="font-semibold">
                          {p.name}{' '}
                          <span className="text-xs font-normal text-ink-soft">
                            {[p.data_type, p.status].filter(Boolean).join(', ')}
                          </span>
                        </p>
                        <p className="mt-1 flex flex-wrap gap-1">
                          {p.values.length > 0 ? (
                            p.values.map((v) => (
                              <span
                                key={v.sf_id}
                                className={`rounded px-1.5 py-0.5 text-xs ${v.is_default ? 'bg-cobalt text-white' : 'bg-cobalt-wash text-cobalt-deep'}`}
                              >
                                {v.label}
                              </span>
                            ))
                          ) : (
                            <span className="text-sm text-ink-soft">No values</span>
                          )}
                        </p>
                      </li>
                    ))}
                </ul>
              </SectionGate>
            )}
          </div>
        </>
      )}
    </main>
  )
}
