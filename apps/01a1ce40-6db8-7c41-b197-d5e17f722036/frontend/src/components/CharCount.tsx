export function CharCount({ value, max }: { value: string; max: number }) {
  const n = value.length
  const near = n > max * 0.9
  return (
    <span
      className={`text-xs tabular-nums ${n > max ? 'font-semibold text-magenta' : near ? 'text-ink' : 'text-ink-soft'}`}
      aria-live="polite"
    >
      {n}/{max}
    </span>
  )
}
