import { useCallback, useEffect, useRef, useState } from 'react'
import { Toaster, toast } from 'sonner'
import client from '@/api/client'
import type { components } from '@/api/schema'
import { ago, errorMessage } from '@/lib/format'
import { useAssetsSync } from '@/hooks/useAssetsSync'
import Header from './components/Header'
import SummaryStrip from './components/SummaryStrip'
import AssetTable from './components/AssetTable'
import AssetPanel from './components/AssetPanel'
import NotesCard from './components/NotesCard'

type Asset = components['schemas']['AssetOut']
type Summary = components['schemas']['AssetSummary']
type Note = components['schemas']['NoteOut']

export default function App() {
  const [assets, setAssets] = useState<Asset[] | null>(null)
  const [assetsError, setAssetsError] = useState<string | null>(null)
  const [assetsLoading, setAssetsLoading] = useState(true)
  const [summary, setSummary] = useState<Summary | null>(null)
  const [summaryError, setSummaryError] = useState<string | null>(null)
  const [notes, setNotes] = useState<Note[] | null>(null)
  const [notesError, setNotesError] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<Asset | null>(null)
  const [detailError, setDetailError] = useState<string | null>(null)
  const [now, setNow] = useState(Date.now())
  const sync = useAssetsSync()
  const autoSynced = useRef(false)

  /** Loads the cached asset list and its summary together so they describe the same rows. */
  const loadAssets = useCallback(async (): Promise<Summary | null> => {
    setAssetsLoading(true)
    const [a, s] = await Promise.all([
      client.GET('/api/assets/'),
      client.GET('/api/assets/summary'),
    ])
    if (a.data) {
      setAssets(a.data)
      setAssetsError(null)
    } else {
      setAssets(null)
      setAssetsError(errorMessage(a.error, `Request failed (${a.response.status})`))
    }
    if (s.data) {
      setSummary(s.data)
      setSummaryError(null)
    } else {
      setSummary(null)
      setSummaryError(errorMessage(s.error, `Request failed (${s.response.status})`))
    }
    setAssetsLoading(false)
    setNow(Date.now())
    return s.data ?? null
  }, [])

  const loadNotes = useCallback(async () => {
    const n = await client.GET('/api/notes/')
    if (n.data) {
      setNotes(n.data)
      setNotesError(null)
    } else {
      setNotesError(errorMessage(n.error, `Request failed (${n.response.status})`))
    }
  }, [])

  const runSync = useCallback(async () => {
    const outcome = await sync.run()
    if (!outcome) return
    if (outcome.ok) {
      await loadAssets()
      toast.success(
        `Synced ${outcome.recordsSynced} asset${outcome.recordsSynced === 1 ? '' : 's'} from Salesforce`,
      )
    } else {
      toast.error('Salesforce sync failed', { description: outcome.reason, duration: 10000 })
    }
  }, [sync, loadAssets])

  useEffect(() => {
    void loadNotes()
    void loadAssets().then((s) => {
      if (s && s.synced_at == null && !autoSynced.current) {
        autoSynced.current = true
        void runSync()
      }
    })
    const t = setInterval(() => setNow(Date.now()), 15000)
    return () => clearInterval(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    setDetail(null)
    setDetailError(null)
    if (!selectedId) return
    let cancelled = false
    client
      .GET('/api/assets/{asset_id}', { params: { path: { asset_id: selectedId } } })
      .then((r) => {
        if (cancelled) return
        if (r.data) setDetail(r.data)
        else setDetailError(errorMessage(r.error, `Request failed (${r.response.status})`))
      })
    return () => {
      cancelled = true
    }
  }, [selectedId])

  async function saveNote(text: string): Promise<string | null> {
    const r = await client.POST('/api/notes/', { body: { text } })
    if (r.error || !r.data) return errorMessage(r.error, `Request failed (${r.response.status})`)
    await loadNotes()
    return null
  }

  const close = useCallback(() => setSelectedId(null), [])
  const selected = detail ?? assets?.find((a) => a.id === selectedId) ?? null

  const syncedLabel = summary
    ? ago(summary.synced_at, now)
    : summaryError
      ? 'last sync unknown'
      : '…'

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Header
        syncedLabel={syncedLabel}
        neverSynced={summary?.synced_at === null || !!summaryError}
        syncing={sync.isRunning}
        onSync={runSync}
      />
      <main className="mx-auto flex max-w-[1280px] flex-col gap-5 px-6 py-6">
        <SummaryStrip summary={summary} error={summaryError} onRetry={loadAssets} />
        <AssetTable
          assets={assets}
          loading={assetsLoading}
          error={assetsError}
          neverSynced={summary?.synced_at === null}
          syncing={sync.isRunning}
          selectedId={selectedId}
          onSelect={setSelectedId}
          onRetry={loadAssets}
        />
        <NotesCard notes={notes} loadError={notesError} onRetry={loadNotes} onSave={saveNote} />
      </main>
      <AssetPanel asset={selectedId ? selected : null} error={detailError} onClose={close} />
      <Toaster position="bottom-right" richColors closeButton />
    </div>
  )
}
