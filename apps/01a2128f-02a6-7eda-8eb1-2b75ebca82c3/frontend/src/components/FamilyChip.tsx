import { familyLabel } from '@/lib/format'

const tones: Record<string, string> = {
  Hardware: 'bg-violet-100 text-violet-700 ring-violet-200',
  Software: 'bg-sky-100 text-sky-700 ring-sky-200',
  Service: 'bg-emerald-100 text-emerald-700 ring-emerald-200',
  Unclassified: 'bg-amber-50 text-amber-700 ring-amber-300 ring-dashed',
}

export default function FamilyChip({ family }: { family: string | null | undefined }) {
  const label = familyLabel(family)
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${tones[label] ?? tones.Unclassified}`}
    >
      {label}
    </span>
  )
}
