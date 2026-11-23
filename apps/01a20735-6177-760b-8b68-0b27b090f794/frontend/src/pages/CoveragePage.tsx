import { useCallback, useEffect, useState } from 'react'
import { Loader2, ShieldCheck } from 'lucide-react'
import client from '@/api/client'
import { StatusPill } from '@/components/catalog/StatusPill'
import { SyncBar } from '@/components/catalog/SyncBar'
import { errorMessage } from '@/lib/notes'
import { SECTION_LABEL, formatDateTime, type CatalogOverview } from '@/lib/catalog'

export default function CoveragePage() {
  const [data, setData] = useState<CatalogOverview | null>(null)
  const [error, setError] = useState<string | null>(null)
  const load = useCallback(async () => {
    const res = await client.GET('/api/catalog/overview')
    if (res.data) {
      setData(res.data)
      setError(null)
    } else setError(errorMessage(res.error, 'Coverage could not be loaded.'))
  }, [])
  useEffect(() => {
    void load()
  }, [load])

  const mapped = data?.coverage.filter((c) => c.mapped) ?? []
  const other = data?.coverage.filter((c) => !c.mapped) ?? []

  return (
    <main className="mx-auto max-w-6xl px-5 py-6 sm:px-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">Coverage and sync</h1>
          <p className="mt-1 max-w-prose text-sm text-ink-soft">
            What the Salesforce connector can read for each Revenue Cloud catalog object, checked on
            every sync. Blocked objects are reported here instead of appearing as empty.
          </p>
        </div>
        <SyncBar status={data?.sync} onFinished={() => void load()} />
      </div>

      <div className="mt-5 rounded-2xl bg-caution-wash p-4 text-sm">
        <p className="flex items-center gap-2 font-semibold">
          <ShieldCheck className="size-4" /> Shared Salesforce connector
        </p>
        <p className="mt-1">
          Every read and every description save runs as the single Salesforce user configured for
          this app’s connector. That’s why the catalog is limited to app admins.
        </p>
      </div>

      {error && (
        <p
          role="alert"
          className="mt-4 rounded-xl border border-magenta bg-magenta-wash p-4 text-sm"
        >
          {error}
        </p>
      )}
      {!data && !error && (
        <p className="mt-6 flex items-center gap-2 text-ink-soft">
          <Loader2 className="size-4 animate-spin" /> Loading…
        </p>
      )}

      {data && (
        <>
          <h2 className="mt-8 text-lg font-bold">Sections</h2>
          <ul className="mt-2 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {data.sections.map((s) => (
              <li
                key={s.section}
                className={`rounded-xl border p-3 ${s.available ? 'border-teal/40 bg-sheet' : 'border-magenta/50 bg-magenta-wash'}`}
              >
                <p className="text-sm font-semibold">{SECTION_LABEL[s.section] ?? s.section}</p>
                <div className="mt-1">
                  <StatusPill status={s.status} />
                </div>
                {!s.available && s.blocked_objects.length > 0 && (
                  <p className="mt-1 text-xs">Blocked: {s.blocked_objects.join(', ')}</p>
                )}
              </li>
            ))}
          </ul>

          {[
            { title: 'Catalog objects shown in this app', rows: mapped },
            { title: 'Other catalog structures checked but not shown yet', rows: other },
          ].map((group) => (
            <section key={group.title} className="mt-8">
              <h2 className="text-lg font-bold">{group.title}</h2>
              <div className="mt-2 overflow-x-auto rounded-2xl border border-line bg-sheet">
                <table className="w-full text-left text-sm">
                  <thead className="bg-paper text-ink-soft">
                    <tr>
                      <th className="px-4 py-2.5 font-semibold">Salesforce object</th>
                      <th className="px-4 py-2.5 font-semibold">Status</th>
                      <th className="px-4 py-2.5 text-right font-semibold">In Salesforce</th>
                      {group.rows === mapped && (
                        <th className="px-4 py-2.5 text-right font-semibold">In app</th>
                      )}
                      <th className="px-4 py-2.5 font-semibold">Notes</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {group.rows.map((c) => (
                      <tr key={c.object_api_name} className="align-top">
                        <td className="px-4 py-2.5">
                          <span className="font-semibold">{c.label}</span>
                          <span className="block font-mono text-xs text-ink-soft">
                            {c.object_api_name}
                          </span>
                        </td>
                        <td className="px-4 py-2.5">
                          <StatusPill status={c.status} />
                        </td>
                        <td className="px-4 py-2.5 text-right tabular-nums">
                          {c.salesforce_count ?? '—'}
                        </td>
                        {group.rows === mapped && (
                          <td className="px-4 py-2.5 text-right tabular-nums">{c.cached_count}</td>
                        )}
                        <td className="max-w-md px-4 py-2.5 text-xs text-ink-soft">
                          {c.detail ?? ''}
                          {c.checked_at && (
                            <span className="block">Checked {formatDateTime(c.checked_at)}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ))}
        </>
      )}
    </main>
  )
}
