import { Loader2, RefreshCw, RotateCcw } from 'lucide-react'
import { useCatalogSync } from '@/hooks/useCatalogSync'
import { formatDateTime, type SyncStatus } from '@/lib/catalog'

export function SyncBar({
  status,
  onFinished,
}: {
  status: SyncStatus | undefined
  onFinished: () => void
}) {
  const { isRunning, recordsSynced, error, run } = useCatalogSync(onFinished)
  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="text-sm">
        {isRunning ? (
          <span className="flex items-center gap-2 font-semibold text-cobalt-deep">
            <Loader2 className="size-4 animate-spin" /> Syncing from Salesforce… {recordsSynced}{' '}
            records
          </span>
        ) : status?.has_synced ? (
          <span className="text-ink-soft">
            Last synced{' '}
            <span className="font-semibold text-ink">{formatDateTime(status.last_synced_at)}</span>
          </span>
        ) : (
          <span className="font-semibold text-ink">Not synced yet</span>
        )}
        {!isRunning &&
          status?.last_job_status === 'failed' &&
          status.last_failure_reason &&
          !error && (
            <span className="mt-0.5 block text-magenta-deep">
              Last sync failed: {status.last_failure_reason}
            </span>
          )}
        {error && <span className="mt-0.5 block text-magenta-deep">Sync failed: {error}</span>}
      </div>
      <div className="flex gap-2">
        <button
          type="button"
          disabled={isRunning}
          onClick={() => void run(false)}
          className="inline-flex items-center gap-2 rounded-lg bg-cobalt px-3 py-2 text-sm font-semibold text-white hover:bg-cobalt-deep focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cobalt disabled:opacity-60"
        >
          <RefreshCw className="size-4" /> Sync changes
        </button>
        <button
          type="button"
          disabled={isRunning}
          onClick={() => void run(true)}
          title="Re-read every record and remove ones deleted in Salesforce"
          className="inline-flex items-center gap-2 rounded-lg border border-line bg-sheet px-3 py-2 text-sm font-semibold text-ink hover:bg-paper focus-visible:outline-2 focus-visible:outline-cobalt disabled:opacity-60"
        >
          <RotateCcw className="size-4" /> Full refresh
        </button>
      </div>
    </div>
  )
}
