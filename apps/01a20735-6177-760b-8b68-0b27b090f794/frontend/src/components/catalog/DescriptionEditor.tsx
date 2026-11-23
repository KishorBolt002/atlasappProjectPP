import { useState } from 'react'
import { toast } from 'sonner'
import { AlertTriangle, CheckCircle2, Loader2, Pencil, RefreshCw, X } from 'lucide-react'
import client from '@/api/client'
import { errorMessage } from '@/lib/notes'
import { formatDateTime, type DescriptionPreview, type LiveDescription } from '@/lib/catalog'

type Stage =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'editing'; live: LiveDescription }
  | { kind: 'reviewing'; live: LiveDescription; preview: DescriptionPreview }
  | { kind: 'saving'; live: LiveDescription; preview: DescriptionPreview }

type Props = {
  productId: string
  cachedDescription: string | null
  onSaved: () => void
}

function TextPanel({
  title,
  meta,
  text,
  tone,
}: {
  title: string
  meta?: string
  text: string | null
  tone: 'current' | 'proposed'
}) {
  return (
    <div
      className={`flex min-w-0 flex-col rounded-xl border-2 ${tone === 'current' ? 'border-line bg-paper' : 'border-cobalt bg-sheet'}`}
    >
      <div className="border-b border-line/80 px-4 py-2">
        <p className={`text-sm font-bold ${tone === 'proposed' ? 'text-cobalt-deep' : ''}`}>
          {title}
        </p>
        {meta && <p className="text-xs text-ink-soft">{meta}</p>}
      </div>
      <p className="flex-1 px-4 py-3 text-sm leading-relaxed break-words whitespace-pre-wrap">
        {text ? text : <span className="text-ink-soft italic">Empty</span>}
      </p>
    </div>
  )
}

/** Same count Salesforce/the server uses: code points after newline normalization. */
function charCount(text: string): number {
  return [...text.replace(/\r\n?/g, '\n')].length
}

export function DescriptionEditor({ productId, cachedDescription, onSaved }: Props) {
  const [stage, setStage] = useState<Stage>({ kind: 'idle' })
  const [draft, setDraft] = useState('')
  const [problem, setProblem] = useState<{ message: string; conflict: boolean } | null>(null)

  async function loadLive(keepDraft: boolean) {
    setStage({ kind: 'loading' })
    setProblem(null)
    const { data, error } = await client.GET('/api/catalog/products/{product_id}/description', {
      params: { path: { product_id: productId } },
    })
    if (!data) {
      setStage({ kind: 'idle' })
      setProblem({
        message: errorMessage(error, 'The current description could not be read from Salesforce.'),
        conflict: false,
      })
      return
    }
    if (!keepDraft) setDraft(data.current_description ?? '')
    setStage({ kind: 'editing', live: data })
  }

  async function review(live: LiveDescription) {
    setProblem(null)
    const { data, error } = await client.POST(
      '/api/catalog/products/{product_id}/description/preview',
      {
        params: { path: { product_id: productId } },
        body: { proposed_description: draft },
      },
    )
    if (!data) {
      setProblem({
        message: errorMessage(error, 'The change could not be checked against Salesforce.'),
        conflict: false,
      })
      return
    }
    const fresh: LiveDescription = {
      ...live,
      current_description: data.current_description,
      last_modified: data.last_modified,
    }
    setStage({ kind: 'reviewing', live: fresh, preview: data })
  }

  async function save(live: LiveDescription, preview: DescriptionPreview) {
    setStage({ kind: 'saving', live, preview })
    setProblem(null)
    const { data, error, response } = await client.PUT(
      '/api/catalog/products/{product_id}/description',
      {
        params: { path: { product_id: productId } },
        body: {
          proposed_description: draft,
          expected_last_modified: preview.last_modified,
          confirm: true,
        },
      },
    )
    if (!data) {
      const conflict = response.status === 409
      setProblem({
        message: errorMessage(
          error,
          `Salesforce did not save the description (HTTP ${response.status}).`,
        ),
        conflict,
      })
      setStage({ kind: 'reviewing', live, preview })
      return
    }
    toast.success('Description saved to Salesforce and verified')
    setStage({ kind: 'idle' })
    onSaved()
  }

  const busy = stage.kind === 'loading' || stage.kind === 'saving'

  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h2 className="text-lg font-bold">Description</h2>
        {stage.kind === 'idle' && (
          <button
            type="button"
            onClick={() => void loadLive(false)}
            className="inline-flex items-center gap-2 rounded-lg border border-cobalt px-3 py-1.5 text-sm font-semibold text-cobalt hover:bg-cobalt-wash focus-visible:outline-2 focus-visible:outline-cobalt"
          >
            <Pencil className="size-4" /> Edit description
          </button>
        )}
        {stage.kind === 'loading' && (
          <span className="flex items-center gap-2 text-sm text-ink-soft">
            <Loader2 className="size-4 animate-spin" /> Reading current value from Salesforce…
          </span>
        )}
      </div>

      {stage.kind === 'idle' || stage.kind === 'loading' ? (
        <p className="mt-2 max-w-prose leading-relaxed whitespace-pre-wrap">
          {cachedDescription || (
            <span className="text-ink-soft italic">
              This product has no description in Salesforce.
            </span>
          )}
        </p>
      ) : null}

      {problem && (
        <div
          role="alert"
          className="mt-3 rounded-xl border border-magenta bg-magenta-wash p-4 text-sm"
        >
          <p className="flex items-center gap-2 font-semibold">
            <AlertTriangle className="size-4 text-magenta-deep" />
            {problem.conflict ? 'Changed in Salesforce since you loaded it' : 'Not saved'}
          </p>
          <p className="mt-1">{problem.message}</p>
          {problem.conflict && (
            <button
              type="button"
              onClick={() => void loadLive(true)}
              className="mt-3 inline-flex items-center gap-2 rounded-lg bg-sheet px-3 py-1.5 font-semibold hover:bg-paper"
            >
              <RefreshCw className="size-4" /> Reload current value and keep my text
            </button>
          )}
        </div>
      )}

      {stage.kind === 'editing' && (
        <div className="mt-3 space-y-3">
          {stage.live.cache_was_stale && (
            <p className="rounded-lg bg-caution-wash px-3 py-2 text-sm">
              Salesforce has a newer value than the last sync. The current value below comes
              directly from Salesforce.
            </p>
          )}
          <TextPanel
            title="Current in Salesforce"
            meta={`Last modified ${formatDateTime(stage.live.last_modified)}${stage.live.last_modified_by ? ` by ${stage.live.last_modified_by}` : ''}`}
            text={stage.live.current_description}
            tone="current"
          />
          <label className="block">
            <span className="text-sm font-bold text-cobalt-deep">Proposed description</span>
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              rows={6}
              className="mt-1 w-full rounded-xl border-2 border-cobalt/50 bg-sheet p-3 text-sm leading-relaxed focus:border-cobalt focus:outline-none"
            />
            <span
              className={`text-xs ${charCount(draft) > stage.live.field.max_length ? 'font-semibold text-magenta-deep' : 'text-ink-soft'}`}
            >
              {charCount(draft)} of {stage.live.field.max_length} characters. Saves to{' '}
              {stage.live.field.object_api_name}.{stage.live.field.field_api_name} (
              {stage.live.field.label})
            </span>
          </label>
          {!stage.live.field.updateable && (
            <p className="text-sm font-semibold text-magenta-deep">
              Salesforce reports this field is not editable for the connector user, so it can’t be
              saved from here.
            </p>
          )}
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void review(stage.live)}
              className="rounded-lg bg-cobalt px-4 py-2 text-sm font-semibold text-white hover:bg-cobalt-deep focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cobalt"
            >
              Review change
            </button>
            <button
              type="button"
              onClick={() => {
                setStage({ kind: 'idle' })
                setProblem(null)
              }}
              className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-semibold text-ink-soft hover:bg-paper"
            >
              <X className="size-4" /> Cancel
            </button>
          </div>
        </div>
      )}

      {(stage.kind === 'reviewing' || stage.kind === 'saving') && (
        <div className="mt-3 space-y-3">
          <div className="grid gap-3 md:grid-cols-2">
            <TextPanel
              title="Current in Salesforce"
              meta={`Last modified ${formatDateTime(stage.preview.last_modified)}`}
              text={stage.preview.current_description}
              tone="current"
            />
            <TextPanel
              title="Will be saved"
              meta={`${stage.preview.proposed_length} of ${stage.preview.max_length} characters`}
              text={stage.preview.proposed_description || null}
              tone="proposed"
            />
          </div>
          {stage.preview.clears_description && (
            <p className="rounded-lg bg-caution-wash px-3 py-2 text-sm font-semibold">
              Saving will clear this product’s description in Salesforce.
            </p>
          )}
          {stage.preview.problems.length > 0 && (
            <ul className="space-y-1 rounded-lg bg-magenta-wash px-4 py-3 text-sm">
              {stage.preview.problems.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
          )}
          <p className="text-sm text-ink-soft">
            Only this product’s description changes. Salesforce rejects the save if anyone edits the
            product before you confirm.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={!stage.preview.can_apply || busy}
              onClick={() => void save(stage.live, stage.preview)}
              className="inline-flex items-center gap-2 rounded-lg bg-cobalt px-4 py-2 text-sm font-semibold text-white hover:bg-cobalt-deep focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cobalt disabled:opacity-50"
            >
              {stage.kind === 'saving' ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <CheckCircle2 className="size-4" />
              )}
              Save to Salesforce
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => setStage({ kind: 'editing', live: stage.live })}
              className="rounded-lg border border-line px-3 py-2 text-sm font-semibold hover:bg-paper disabled:opacity-50"
            >
              Keep editing
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => {
                setStage({ kind: 'idle' })
                setProblem(null)
              }}
              className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-semibold text-ink-soft hover:bg-paper disabled:opacity-50"
            >
              <X className="size-4" /> Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
