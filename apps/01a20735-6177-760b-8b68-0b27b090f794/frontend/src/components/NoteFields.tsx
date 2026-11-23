import { CharCount } from './CharCount'
import { BODY_MAX, TITLE_MAX } from '@/lib/notes'

type Props = {
  idPrefix: string
  title: string
  body: string
  onTitle: (v: string) => void
  onBody: (v: string) => void
  disabled?: boolean
  autoFocus?: boolean
  rows?: number
}

const field =
  'w-full rounded-lg border border-line bg-white px-3 py-2 text-[15px] text-ink placeholder:text-ink-soft/70 focus:border-cobalt focus:outline-none focus:ring-3 focus:ring-cobalt/20 disabled:opacity-60'

export function NoteFields({
  idPrefix,
  title,
  body,
  onTitle,
  onBody,
  disabled,
  autoFocus,
  rows = 5,
}: Props) {
  return (
    <div className="space-y-4">
      <div>
        <div className="mb-1.5 flex items-baseline justify-between">
          <label htmlFor={`${idPrefix}-title`} className="text-sm font-semibold">
            Title
          </label>
          <CharCount value={title} max={TITLE_MAX} />
        </div>
        <input
          id={`${idPrefix}-title`}
          className={field}
          value={title}
          maxLength={TITLE_MAX}
          onChange={(e) => onTitle(e.target.value)}
          disabled={disabled}
          autoFocus={autoFocus}
          placeholder="Sync check #1"
          autoComplete="off"
        />
      </div>
      <div>
        <div className="mb-1.5 flex items-baseline justify-between">
          <label htmlFor={`${idPrefix}-body`} className="text-sm font-semibold">
            Text
          </label>
          <CharCount value={body} max={BODY_MAX} />
        </div>
        <textarea
          id={`${idPrefix}-body`}
          className={`${field} resize-y leading-relaxed`}
          value={body}
          maxLength={BODY_MAX}
          rows={rows}
          onChange={(e) => onBody(e.target.value)}
          disabled={disabled}
          placeholder="Any sample text works here."
        />
      </div>
    </div>
  )
}
