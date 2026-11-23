import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'
import { AlertTriangle, Loader2, RefreshCw } from 'lucide-react'
import client from '@/api/client'
import { NoteComposer } from '@/components/NoteComposer'
import { NoteItem } from '@/components/NoteItem'
import { errorMessage, type Note } from '@/lib/notes'

type LoadState = { status: 'loading' } | { status: 'error'; message: string } | { status: 'ready' }

export default function NotesPage() {
  const [notes, setNotes] = useState<Note[]>([])
  const [load, setLoad] = useState<LoadState>({ status: 'loading' })

  const fetchNotes = useCallback(async () => {
    setLoad({ status: 'loading' })
    try {
      const { data, error } = await client.GET('/api/notes/')
      if (error || !data) {
        setLoad({
          status: 'error',
          message: errorMessage(error, 'The server didn’t return the notes.'),
        })
        return
      }
      setNotes(data)
      setLoad({ status: 'ready' })
    } catch (e) {
      setLoad({ status: 'error', message: errorMessage(e, 'Couldn’t reach the server.') })
    }
  }, [])

  useEffect(() => {
    void fetchNotes()
  }, [fetchNotes])

  async function createNote(title: string, body: string): Promise<boolean> {
    try {
      const { data, error } = await client.POST('/api/notes/', { body: { title, body } })
      if (error || !data) {
        toast.error(`Note not added: ${errorMessage(error, 'unknown server error')}`)
        return false
      }
      setNotes((prev) => [data, ...prev])
      toast.success('Note added')
      return true
    } catch (e) {
      toast.error(`Note not added: ${errorMessage(e, 'couldn’t reach the server')}`)
      return false
    }
  }

  async function saveNote(id: number, title: string, body: string): Promise<boolean> {
    try {
      const { data, error } = await client.PUT('/api/notes/{note_id}', {
        params: { path: { note_id: id } },
        body: { title, body },
      })
      if (error || !data) {
        toast.error(`Changes not saved: ${errorMessage(error, 'unknown server error')}`)
        return false
      }
      setNotes((prev) => prev.map((n) => (n.id === id ? data : n)))
      toast.success('Changes saved')
      return true
    } catch (e) {
      toast.error(`Changes not saved: ${errorMessage(e, 'couldn’t reach the server')}`)
      return false
    }
  }

  async function deleteNote(id: number): Promise<boolean> {
    try {
      const { error, response } = await client.DELETE('/api/notes/{note_id}', {
        params: { path: { note_id: id } },
      })
      if (error || !response.ok) {
        toast.error(
          `Note not deleted: ${errorMessage(error, `server responded ${response.status}`)}`,
        )
        return false
      }
      setNotes((prev) => prev.filter((n) => n.id !== id))
      toast.success('Note deleted')
      return true
    } catch (e) {
      toast.error(`Note not deleted: ${errorMessage(e, 'couldn’t reach the server')}`)
      return false
    }
  }

  return (
    <>
      <div className="caution-tape">
        <p className="mx-auto flex max-w-6xl items-center gap-2 px-5 py-2.5 text-sm font-semibold text-ink sm:px-8">
          <AlertTriangle className="size-4 shrink-0" />
          Throwaway test notes. Don’t enter real business, patient, or customer data here.
        </p>
      </div>
      <main className="mx-auto grid max-w-6xl gap-8 px-5 py-8 sm:px-8 lg:grid-cols-[minmax(0,360px)_minmax(0,1fr)] lg:gap-10">
        <aside className="lg:sticky lg:top-8 lg:self-start">
          <NoteComposer onCreate={createNote} />
        </aside>

        <section aria-labelledby="notes-heading">
          <div className="mb-4 flex items-baseline justify-between">
            <h2 id="notes-heading" className="text-lg font-bold tracking-tight">
              Notes
              {load.status === 'ready' && (
                <span className="ml-2 font-medium text-ink-soft">{notes.length}</span>
              )}
            </h2>
            <span className="text-sm text-ink-soft">Newest first</span>
          </div>

          {load.status === 'loading' && (
            <div className="flex items-center gap-2 rounded-2xl border border-line bg-sheet p-6 text-ink-soft">
              <Loader2 className="size-4 animate-spin" /> Loading notes…
            </div>
          )}

          {load.status === 'error' && (
            <div role="alert" className="rounded-2xl border border-magenta bg-magenta-wash p-6">
              <p className="font-semibold">Notes couldn’t be loaded.</p>
              <p className="mt-1 text-sm text-ink-soft">{load.message}</p>
              <button
                type="button"
                onClick={() => void fetchNotes()}
                className="mt-4 inline-flex items-center gap-2 rounded-lg bg-white px-3 py-2 text-sm font-semibold text-ink hover:bg-paper focus-visible:outline-2 focus-visible:outline-cobalt"
              >
                <RefreshCw className="size-4" /> Try again
              </button>
            </div>
          )}

          {load.status === 'ready' && notes.length === 0 && (
            <div className="rounded-2xl border-2 border-dashed border-line px-6 py-14 text-center">
              <p className="font-semibold">No notes yet</p>
              <p className="mt-1 text-sm text-ink-soft">Add one with the form to start the test.</p>
            </div>
          )}

          {load.status === 'ready' && notes.length > 0 && (
            <ul className="space-y-4">
              {notes.map((n) => (
                <NoteItem key={n.id} note={n} onSave={saveNote} onDelete={deleteNote} />
              ))}
            </ul>
          )}
        </section>
      </main>
    </>
  )
}
