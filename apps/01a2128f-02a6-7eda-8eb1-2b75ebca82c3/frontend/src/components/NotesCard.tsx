import { useState } from 'react'
import { NotebookPen } from 'lucide-react'
import type { components } from '@/api/schema'
import { dateTime } from '@/lib/format'
import { ErrorBlock, LoadingBlock } from './StateBlocks'

type Note = components['schemas']['NoteOut']

const MAX = 500

export default function NotesCard({
  notes,
  loadError,
  onRetry,
  onSave,
}: {
  notes: Note[] | null
  loadError: string | null
  onRetry: () => void
  /** Resolves to null on success, or the server's error message. */
  onSave: (text: string) => Promise<string | null>
}) {
  const [text, setText] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    const value = text.trim()
    if (!value || saving) return
    setSaving(true)
    setSaveError(null)
    const err = await onSave(value)
    if (err) setSaveError(err)
    else setText('')
    setSaving(false)
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center gap-2.5 px-5 py-3.5">
        <span className="grid size-8 place-items-center rounded-lg bg-amber-100 text-amber-600">
          <NotebookPen className="size-4" />
        </span>
        <div>
          <h2 className="text-base font-semibold text-slate-900">Test notes</h2>
          <p className="text-xs text-slate-500">Saved to the app's own database</p>
        </div>
      </div>
      <div className="grid gap-5 border-t border-slate-100 p-5 md:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <form onSubmit={submit} className="flex flex-col gap-2.5">
          <label htmlFor="note" className="text-sm font-medium text-slate-700">
            Add a note
          </label>
          <textarea
            id="note"
            data-walkthrough="note-input"
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={MAX}
            rows={3}
            placeholder="e.g. Custom domain loads over HTTPS"
            aria-invalid={saveError ? true : undefined}
            aria-describedby={saveError ? 'note-error' : undefined}
            className="resize-none rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-600 focus:outline-2 focus:outline-blue-600/30"
          />
          {saveError && (
            <p id="note-error" role="alert" className="text-xs text-red-700">
              Couldn't save the note: {saveError}
            </p>
          )}
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500">
              {text.length}/{MAX}
            </span>
            <button
              type="submit"
              disabled={!text.trim() || saving}
              className="rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:bg-slate-200 disabled:text-slate-500 disabled:shadow-none"
            >
              {saving ? 'Saving…' : 'Save note'}
            </button>
          </div>
        </form>
        {loadError ? (
          <ErrorBlock title="Couldn't load notes" message={loadError} onRetry={onRetry} />
        ) : notes === null ? (
          <LoadingBlock label="Loading notes…" />
        ) : (
          <ul className="max-h-56 space-y-2 overflow-y-auto">
            {notes.length === 0 && (
              <li className="rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500">
                No notes yet. Write one and save it to see it here.
              </li>
            )}
            {notes.map((n) => (
              <li key={n.id} className="rounded-lg bg-slate-50 px-3.5 py-2.5">
                <p className="whitespace-pre-wrap break-words text-sm text-slate-900">{n.text}</p>
                <time dateTime={n.created_at} className="text-xs text-slate-500">
                  {dateTime(n.created_at)}
                </time>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
