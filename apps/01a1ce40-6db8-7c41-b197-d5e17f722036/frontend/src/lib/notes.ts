import type { components } from '@/api/schema'

export type Note = components['schemas']['NoteResponse']
export type NoteCreate = components['schemas']['NoteCreate']

export const TITLE_MAX = 200
export const BODY_MAX = 2000

/** Turn an openapi-fetch error payload into a readable message. */
export function errorMessage(error: unknown, fallback: string): string {
  if (error && typeof error === 'object' && 'detail' in error) {
    const detail = (error as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      const msgs = detail
        .map((d) => (d && typeof d === 'object' && 'msg' in d ? String(d.msg) : ''))
        .filter(Boolean)
      if (msgs.length) return msgs.join('; ')
    }
  }
  if (error instanceof Error) return error.message
  return fallback
}

const fmt = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'short',
})

export function formatTime(iso: string): string {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : fmt.format(d)
}
