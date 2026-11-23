import { useCallback, useState } from 'react'
import client from '@/api/client'
import { errorMessage } from '@/lib/notes'

/** Browser-driven catalog sync. Running state is local on purpose (auto-heal contract). */
export function useCatalogSync(onFinished: () => void) {
  const [isRunning, setIsRunning] = useState(false)
  const [recordsSynced, setRecordsSynced] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const run = useCallback(
    async (full: boolean) => {
      if (isRunning) return
      setIsRunning(true)
      setError(null)
      setRecordsSynced(0)
      try {
        const start = full
          ? await client.POST('/api/sync/catalog/start-full', {})
          : await client.POST('/api/sync/catalog/start', {})
        if (!start.data) {
          setError(errorMessage(start.error, 'The sync could not start.'))
          return
        }
        const id = start.data.id
        while (true) {
          const tick = await client.POST('/api/sync/catalog/{job_id}/tick', {
            params: { path: { job_id: id } },
          })
          if (!tick.data) {
            setError(
              errorMessage(tick.error, 'The sync stopped responding. Run it again to resume.'),
            )
            break
          }
          setRecordsSynced(tick.data.records_synced)
          if (tick.data.finished) {
            if (tick.data.failure_reason) setError(tick.data.failure_reason)
            break
          }
        }
      } catch (e) {
        setError(errorMessage(e, 'Couldn’t reach the server. Run the sync again to resume.'))
      } finally {
        setIsRunning(false)
        onFinished()
      }
    },
    [isRunning, onFinished],
  )

  return { isRunning, recordsSynced, error, run }
}
