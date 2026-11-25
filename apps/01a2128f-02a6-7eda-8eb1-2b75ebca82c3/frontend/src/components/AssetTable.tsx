import type { components } from '@/api/schema'
import { money, renewal, shortDate, text } from '@/lib/format'
import FamilyChip from './FamilyChip'
import { ErrorBlock, LoadingBlock } from './StateBlocks'

type Asset = components['schemas']['AssetOut']

const heads = [
  'Asset',
  'Account',
  'Product code',
  'Product family',
  'Lifecycle value (USD)',
  'MRR (USD)',
  'Lifecycle start',
  'Lifecycle end',
  'Renewal',
]
const numeric = new Set([4, 5])

export default function AssetTable({
  assets,
  loading,
  error,
  neverSynced,
  syncing,
  selectedId,
  onSelect,
  onRetry,
}: {
  assets: Asset[] | null
  loading: boolean
  error: string | null
  neverSynced: boolean
  syncing: boolean
  selectedId: string | null
  onSelect: (id: string) => void
  onRetry: () => void
}) {
  let body: React.ReactNode = null
  if (error) {
    body = <ErrorBlock title="Couldn't load assets" message={error} onRetry={onRetry} />
  } else if (loading && !assets) {
    body = <LoadingBlock label="Loading assets…" />
  } else if (assets && assets.length === 0) {
    body = syncing ? (
      <LoadingBlock label="Syncing assets from Salesforce…" />
    ) : (
      <div className="m-4 rounded-lg border border-dashed border-slate-300 px-4 py-8 text-center text-sm text-slate-500">
        {neverSynced
          ? "Assets haven't been synced from Salesforce yet. Use Sync to load them."
          : 'Salesforce returned no assets on the last sync.'}
      </div>
    )
  }

  return (
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-baseline justify-between px-5 py-3.5">
        <h2 className="text-base font-semibold text-slate-900">Recently created assets</h2>
        <span className="text-sm text-slate-500">Latest 10 · select a row for details</span>
      </div>
      {body ?? (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[980px] text-left text-sm">
            <thead>
              <tr className="border-y border-slate-200 bg-slate-50 text-xs font-medium text-slate-500">
                {heads.map((h, i) => (
                  <th
                    key={h}
                    className={`px-4 py-2.5 font-medium ${numeric.has(i) ? 'text-right' : ''}`}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(assets ?? []).map((a, i) => (
                <tr
                  key={a.id}
                  data-walkthrough={i === 0 ? 'asset-row' : undefined}
                  tabIndex={0}
                  onClick={() => onSelect(a.id)}
                  onKeyDown={(e) => e.key === 'Enter' && onSelect(a.id)}
                  className={`cursor-pointer border-b border-slate-100 transition-colors last:border-0 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-blue-600 ${
                    selectedId === a.id ? 'bg-blue-50' : 'hover:bg-blue-50/60'
                  }`}
                >
                  <td className="px-4 py-3 font-medium text-slate-900">{text(a.name)}</td>
                  <td className="px-4 py-3 text-slate-700">{text(a.account)}</td>
                  <td className="px-4 py-3 font-medium text-blue-700">{text(a.product_code)}</td>
                  <td className="px-4 py-3">
                    <FamilyChip family={a.family} />
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-900">
                    {money(a.lifecycle_value)}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-900">
                    {money(a.mrr)}
                  </td>
                  <td className="px-4 py-3 text-slate-700">{shortDate(a.lifecycle_start)}</td>
                  <td className="px-4 py-3 text-slate-700">{shortDate(a.lifecycle_end)}</td>
                  <td className="px-4 py-3 text-slate-700">
                    {renewal(a.renewal_term, a.renewal_unit)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
