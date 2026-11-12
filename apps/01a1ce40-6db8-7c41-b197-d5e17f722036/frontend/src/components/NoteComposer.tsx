import { useState, type FormEvent } from 'react'
import { Loader2, Plus } from 'lucide-react'
import { NoteFields } from './NoteFields'
import { BODY_MAX, TITLE_MAX } from '@/lib/notes'

type Props = { onCreate: (title: string, body: string) => Promise<boolean> }

export function NoteComposer({ onCreate }: Props) {
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [saving, setSaving] = useState(false)

  const t = title.trim()
  const b = body.trim()
  const valid = t.length > 0 && b.length > 0 && t.length <= TITLE_MAX && b.length <= BODY_MAX

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!valid || saving) return
    setSaving(true)
    const ok = await onCreate(t, b)
    setSaving(false)
    if (ok) {
      setTitle('')
      setBody('')
    }
  }

  return (
    <form onSubmit={submit} className="rounded-2xl border border-line bg-sheet p-5 sm:p-6">
      <h2 className="mb-4 text-lg font-bold tracking-tight">Add a note</h2>
      <NoteFields
        idPrefix="new"
        title={title}
        body={body}
        onTitle={setTitle}
        onBody={setBody}
        disabled={saving}
      />
      <button
        type="submit"
        disabled={!valid || saving}
        className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-cobalt px-4 py-2.5 font-semibold text-white transition-colors hover:bg-cobalt-deep focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-cobalt disabled:cursor-not-allowed disabled:bg-cobalt/40"
      >
        {saving ? <Loader2 className="size-4 animate-spin" /> : <Plus className="size-4" />}
        {saving ? 'Adding…' : 'Add note'}
      </button>
    </form>
  )
}
