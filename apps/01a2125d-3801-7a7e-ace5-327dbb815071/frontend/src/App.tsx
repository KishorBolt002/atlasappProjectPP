import { useState, type FormEvent, type KeyboardEvent } from 'react'

export default function App() {
  const [input, setInput] = useState('')
  const [output, setOutput] = useState('')
  const [submitCount, setSubmitCount] = useState(0)

  const submit = () => {
    setOutput(input)
    setSubmitCount((n) => n + 1)
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    submit()
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <main className="flex min-h-screen items-start justify-center px-5 py-14 sm:items-center sm:px-8 sm:py-20">
      <div className="w-full max-w-2xl">
        <header className="mb-10">
          <h1 className="text-3xl font-bold tracking-tight text-ink sm:text-4xl">Submit test</h1>
          <p className="mt-3 max-w-prose text-base leading-relaxed text-slate">
            Type something, submit it, and the output shows exactly what was sent.
          </p>
        </header>

        <form onSubmit={handleSubmit} className="flex flex-col gap-8">
          <div className="flex flex-col gap-3">
            <label htmlFor="input-box" className="text-base font-semibold text-ink">
              Input
            </label>
            <textarea
              id="input-box"
              name="input"
              rows={6}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              aria-describedby="input-hint"
              className="min-h-40 w-full resize-y rounded-xl border-2 border-line bg-surface px-4 py-3.5 text-base leading-relaxed text-ink shadow-[0_1px_0_rgba(16,22,50,0.04)] transition-colors placeholder:text-slate/70 hover:border-[#bfcbe8] focus:outline-none focus-visible:border-accent focus-visible:ring-4 focus-visible:ring-accent/25"
              placeholder="Write a few lines…"
            />
            <p id="input-hint" className="text-sm text-slate">
              Press Ctrl+Enter or ⌘+Enter to submit from the keyboard.
            </p>
          </div>

          <button
            type="submit"
            className="self-stretch rounded-xl bg-accent px-8 py-4 text-lg font-semibold text-white shadow-[0_8px_24px_-8px_rgba(28,92,255,0.6)] transition-[background-color,transform] hover:bg-accent-deep active:translate-y-px focus:outline-none focus-visible:ring-4 focus-visible:ring-accent/40 focus-visible:ring-offset-2 focus-visible:ring-offset-sky sm:self-start"
          >
            Submit
          </button>

          <div className="flex flex-col gap-3">
            <label
              id="output-label"
              htmlFor="output-box"
              className="text-base font-semibold text-ink"
            >
              Output
            </label>
            <output
              key={submitCount}
              id="output-box"
              htmlFor="input-box"
              aria-labelledby="output-label"
              aria-live="polite"
              className={`block min-h-40 w-full whitespace-pre-wrap break-words rounded-xl border-2 border-line border-l-accent border-l-[6px] bg-surface px-4 py-3.5 text-base leading-relaxed text-ink empty:before:text-slate/80 empty:before:content-['Nothing_submitted_yet.'] ${submitCount > 0 ? 'output-flash' : ''}`}
            >
              {output}
            </output>
          </div>
        </form>
      </div>
    </main>
  )
}
