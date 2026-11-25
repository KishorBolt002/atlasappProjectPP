import { CircleDollarSign, Layers, Repeat } from 'lucide-react'
import type { components } from '@/api/schema'
import { money } from '@/lib/format'
import { ErrorBlock } from './StateBlocks'

type Summary = components['schemas']['AssetSummary']

export default function SummaryStrip({
  summary,
  error,
  onRetry,
}: {
  summary: Summary | null
  error: string | null
  onRetry: () => void
}) {
  if (error) {
    return (
      <section
        data-walkthrough="summary"
        className="rounded-xl border border-slate-200 bg-white shadow-sm"
      >
        <ErrorBlock title="Couldn't load the asset summary" message={error} onRetry={onRetry} />
      </section>
    )
  }
  const cells = [
    {
      label: 'Assets',
      value: summary ? String(summary.asset_count) : '…',
      icon: Layers,
      tone: 'bg-blue-100 text-blue-600',
    },
    {
      label: 'Total lifecycle value',
      value: summary ? money(summary.total_lifecycle_value) : '…',
      icon: CircleDollarSign,
      tone: 'bg-fuchsia-100 text-fuchsia-600',
    },
    {
      label: 'Total current MRR',
      value: summary ? money(summary.total_mrr) : '…',
      icon: Repeat,
      tone: 'bg-emerald-100 text-emerald-600',
    },
  ]
  return (
    <section
      data-walkthrough="summary"
      aria-busy={!summary}
      className="grid grid-cols-1 divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white shadow-sm sm:grid-cols-3 sm:divide-x sm:divide-y-0"
    >
      {cells.map(({ label, value, icon: Icon, tone }) => (
        <div key={label} className="flex items-center gap-3 px-5 py-3.5">
          <span className={`grid size-9 shrink-0 place-items-center rounded-lg ${tone}`}>
            <Icon className="size-5" />
          </span>
          <div>
            <div className="text-xs text-slate-500">{label}</div>
            <div
              className={`text-xl font-semibold tabular-nums ${summary ? 'text-slate-900' : 'animate-pulse text-slate-400'}`}
            >
              {value}
            </div>
          </div>
        </div>
      ))}
    </section>
  )
}
