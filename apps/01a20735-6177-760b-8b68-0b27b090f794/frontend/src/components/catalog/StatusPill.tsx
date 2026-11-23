import { STATUS_LABEL, type CoverageStatus } from '@/lib/catalog'

const TONE: Record<CoverageStatus, string> = {
  synced: 'bg-teal-wash text-teal-deep',
  empty: 'bg-paper text-ink-soft ring-1 ring-line',
  not_mapped: 'bg-cobalt-wash text-cobalt-deep',
  not_available: 'bg-paper text-ink-soft ring-1 ring-line',
  blocked: 'bg-magenta-wash text-magenta-deep',
  error: 'bg-magenta-wash text-magenta-deep',
  never_synced: 'bg-caution-wash text-ink',
}

export function StatusPill({ status }: { status: CoverageStatus }) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap ${TONE[status]}`}
    >
      {STATUS_LABEL[status]}
    </span>
  )
}
