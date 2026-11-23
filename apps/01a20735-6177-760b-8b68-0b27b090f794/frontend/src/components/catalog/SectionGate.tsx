import type { ReactNode } from 'react'
import { ShieldAlert } from 'lucide-react'
import { Link } from 'react-router'
import { SECTION_LABEL, section, type SectionAvailability } from '@/lib/catalog'

/** Renders children only when the Salesforce objects behind a section were readable. */
export function SectionGate({
  sections,
  name,
  children,
}: {
  sections: SectionAvailability[] | undefined
  name: string
  children: ReactNode
}) {
  const s = section(sections, name)
  if (!s || s.available) return <>{children}</>
  const never = s.status === 'never_synced'
  return (
    <div
      role="status"
      className={`rounded-xl border-2 border-dashed p-4 ${never ? 'border-line bg-paper' : 'border-magenta/60 bg-magenta-wash'}`}
    >
      <p className="flex items-center gap-2 font-semibold">
        <ShieldAlert className={`size-4 ${never ? 'text-ink-soft' : 'text-magenta-deep'}`} />
        {SECTION_LABEL[name] ?? name} {never ? 'not synced yet' : 'unavailable'}
      </p>
      <p className="mt-1 text-sm text-ink-soft">
        {never
          ? 'Run a catalog sync to read this from Salesforce.'
          : `Salesforce did not allow the connector to read ${s.blocked_objects.join(', ')}. This is not the same as having no data.`}
      </p>
      {s.detail && !never && <p className="mt-1 text-xs text-ink-soft">{s.detail}</p>}
      <Link to="/catalog/coverage" className="mt-2 inline-block text-sm font-semibold text-cobalt">
        See coverage details
      </Link>
    </div>
  )
}
