import { useCallback, useRef, useState } from 'react'
import client from '@/api/client'
import { errorMessage } from '@/lib/format'

export type SyncOutcome = { ok: true; recordsSynced: number } | { ok: false; reason: string }

/**
 * Drives the assets sync runner from the browser: start, then tick until finished.
 * isRunning is local state only (auto-heal contract) — never derived from the job row.
 */
export function useAssetsSync() {
  const [isRunning, setIsRunning] = useState(false)
  const [recordsSynced, setRecordsSynced] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const running = useRef(false)

  const run = useCallback(async (): Promise<SyncOutcome | null> => {
    if (running.current) return null
    running.current = true
    setIsRunning(true)
    setError(null)
    setRecordsSynced(0)
    let outcome: SyncOutcome
    try {
      const start = await client.POST('/api/assets/sync/start', {})
      if (!start.data) throw new Error(errorMessage(start.error, 'Could not start the sync.'))
      const id = start.data.id
      while (true) {
        const tick = await client.POST('/api/assets/sync/{job_id}/tick', {
          params: { path: { job_id: id } },
        })
        if (!tick.data) throw new Error(errorMessage(tick.error, 'The sync stopped unexpectedly.'))
        const view = tick.data
        setRecordsSynced(view.records_synced)
        if (view.finished) {
          outcome =
            view.status === 'success'
              ? { ok: true, recordsSynced: view.records_synced }
              : { ok: false, reason: view.failure_reason || 'The sync failed.' }
          break
        }
      }
    } catch (e) {
      outcome = { ok: false, reason: errorMessage(e, 'The sync failed.') }
    } finally {
      running.current = false
      setIsRunning(false)
    }
    if (!outcome.ok) setError(outcome.reason)
    return outcome
  }, [])

  return { isRunning, recordsSynced, error, run }
}
