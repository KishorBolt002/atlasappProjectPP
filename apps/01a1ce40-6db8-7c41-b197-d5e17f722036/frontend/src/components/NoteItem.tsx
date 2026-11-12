import { useState } from 'react'
import { Check, Loader2, Pencil, Trash2, X } from 'lucide-react'
import { NoteFields } from './NoteFields'
import { BODY_MAX, TITLE_MAX, formatTime, type Note } from '@/lib/notes'

type Props = {
  note: Note
  onSave: (id: number, title: string, body: string) => Promise<boolean>
  onDelete: (id: number) => Promise<boolean>
}

const ghostBtn =
  'inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-cobalt disabled:opacity-50'

export function NoteItem({ note, onSave, onDelete }: Props) {
  const [mode, setMode] = useState<'view' | 'edit' | 'confirm'>('view')
  const [title, setTitle] = useState(note.title)
  const [body, setBody] = useState(note.body)
  const [busy, setBusy] = useState(false)

  const t = title.trim()
  const b = body.trim()
  const valid = t.length > 0 && b.length > 0 && t.length <= TITLE_MAX && b.length <= BODY_MAX
  const changed = t !== note.title || b !== note.body
  const edited = note.updated_at !== note.created_at

  function startEdit() {
    setTitle(note.title)
    setBody(note.body)
    setMode('edit')
  }

  async function save() {
    if (!valid || busy) return
    setBusy(true)
    const ok = await onSave(note.id, t, b)
    setBusy(false)
    if (ok) setMode('view')
  }

  async function remove() {
    setBusy(true)
    const ok = await onDelete(note.id)
    // On success the item unmounts; only reset on failure.
    if (!ok) {
      setBusy(false)
      setMode('view')
    }
  }

  return (
    <li
      className={`rounded-2xl border bg-sheet p-5 sm:p-6 ${mode === 'edit' ? 'border-cobalt ring-3 ring-cobalt/15' : mode === 'confirm' ? 'border-magenta' : 'border-line'}`}
    >
      {mode === 'edit' ? (
        <div>
          <NoteFields
            idPrefix={`note-${note.id}`}
            title={title}
            body={body}
            onTitle={setTitle}
            onBody={setBody}
            disabled={busy}
            autoFocus
            rows={4}
          />
          <div className="mt-4 flex flex-wrap justify-end gap-2">
            <button
              type="button"
              onClick={() => setMode('view')}
              disabled={busy}
              className={`${ghostBtn} text-ink-soft hover:bg-paper`}
            >
              <X className="size-4" /> Cancel
            </button>
            <button
              type="button"
              onClick={save}
              disabled={!valid || !changed || busy}
              className={`${ghostBtn} bg-cobalt text-white hover:bg-cobalt-deep disabled:bg-cobalt/40`}
            >
              {busy ? <Loader2 className="size-4 animate-spin" /> : <Check className="size-4" />}
              Save changes
            </button>
          </div>
        </div>
      ) : (
        <article>
          <div className="flex items-start justify-between gap-4">
            <h3 className="min-w-0 text-lg font-bold leading-snug tracking-tight break-words">
              {note.title}
            </h3>
            {mode === 'view' && (
              <div className="-mr-2 -mt-1 flex shrink-0 gap-1">
                <button
                  type="button"
                  onClick={startEdit}
                  className={`${ghostBtn} text-cobalt hover:bg-cobalt-wash`}
                  aria-label={`Edit ${note.title}`}
                >
                  <Pencil className="size-4" /> <span className="hidden sm:inline">Edit</span>
                </button>
                <button
                  type="button"
                  onClick={() => setMode('confirm')}
                  className={`${ghostBtn} text-magenta hover:bg-magenta-wash`}
                  aria-label={`Delete ${note.title}`}
                >
                  <Trash2 className="size-4" /> <span className="hidden sm:inline">Delete</span>
                </button>
              </div>
            )}
          </div>
          <p className="mt-2 max-w-[68ch] whitespace-pre-wrap break-words leading-relaxed text-ink">
            {note.body}
          </p>
          <p className="mt-4 text-xs text-ink-soft">
            Created {formatTime(note.created_at)}
            {edited && <> &nbsp;/&nbsp; Updated {formatTime(note.updated_at)}</>}
          </p>
          {mode === 'confirm' && (
            <div
              role="alertdialog"
              aria-label="Confirm delete"
              className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-lg bg-magenta-wash px-4 py-3"
            >
              <span className="text-sm font-semibold text-ink">
                Delete this note? This can’t be undone.
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setMode('view')}
                  disabled={busy}
                  className={`${ghostBtn} bg-white text-ink hover:bg-paper`}
                >
                  Keep note
                </button>
                <button
                  type="button"
                  onClick={remove}
                  disabled={busy}
                  className={`${ghostBtn} bg-magenta text-white hover:bg-magenta/90`}
                  autoFocus
                >
                  {busy ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Trash2 className="size-4" />
                  )}
                  Delete note
                </button>
              </div>
            </div>
          )}
        </article>
      )}
    </li>
  )
}
