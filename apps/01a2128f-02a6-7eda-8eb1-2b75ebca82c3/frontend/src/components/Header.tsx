import { Boxes, Cloud, RefreshCw } from 'lucide-react'

export default function Header({
  syncedLabel,
  neverSynced,
  syncing,
  onSync,
}: {
  syncedLabel: string
  neverSynced?: boolean
  syncing: boolean
  onSync: () => void
}) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-6 py-3.5">
      <div className="flex items-center gap-3">
        <span className="grid size-9 place-items-center rounded-xl bg-gradient-to-br from-blue-600 to-fuchsia-500 text-white shadow-sm">
          <Boxes className="size-5" />
        </span>
        <h1 className="text-lg font-semibold tracking-tight text-slate-900">Asset Viewer</h1>
      </div>
      <div className="flex items-center gap-3">
        <span className="inline-flex items-center gap-1.5 text-sm text-slate-600">
          <Cloud className="size-4 text-sky-500" />
          {neverSynced ? 'Salesforce' : 'Synced from Salesforce'} · {syncedLabel}
        </span>
        <button
          data-walkthrough="sync"
          onClick={onSync}
          disabled={syncing}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-70"
        >
          <RefreshCw className={`size-4 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Syncing…' : 'Sync'}
        </button>
      </div>
    </header>
  )
}
