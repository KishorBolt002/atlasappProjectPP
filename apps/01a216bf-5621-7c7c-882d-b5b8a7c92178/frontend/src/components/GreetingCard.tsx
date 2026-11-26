import { useEffect, useState } from 'react'
import { Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import client from '@/api/client'
import type { components } from '@/api/schema'

type Greeting = components['schemas']['Greeting']

const DEFAULT_GREETING: Greeting = {
  message: 'Hello, World!',
  subtitle: 'Your first Atlas app is up and running. Type a name to say hello to someone else.',
}

export default function GreetingCard() {
  const [name, setName] = useState('')
  const [greeting, setGreeting] = useState<Greeting>(DEFAULT_GREETING)

  useEffect(() => {
    let active = true
    client
      .GET('/api/greeting', { params: { query: { name: name.trim() || undefined } } })
      .then(({ data, error }) => {
        if (!active) return
        if (data) {
          setGreeting(data)
        } else {
          console.warn('Greeting request failed', error)
          toast.error("Couldn't update the greeting. Please try again.", { id: 'greeting-error' })
        }
      })
      .catch((err: unknown) => {
        if (!active) return
        console.warn('Greeting request failed', err)
        toast.error("Couldn't reach the greeting service. Please try again.", {
          id: 'greeting-error',
        })
      })
    return () => {
      active = false
    }
  }, [name])

  return (
    <div className="relative z-10 flex w-full max-w-xl flex-col items-center text-center">
      <div className="mb-8 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-fuchsia-500 to-orange-400 text-white shadow-lg shadow-fuchsia-300/60">
        <Sparkles size={26} />
      </div>
      <h1
        data-walkthrough="greeting"
        className="bg-gradient-to-r from-blue-600 via-fuchsia-500 to-orange-500 bg-clip-text pb-2 text-5xl font-bold tracking-tight text-transparent sm:text-7xl"
      >
        {greeting.message}
      </h1>
      <p className="mt-4 max-w-md text-lg leading-relaxed text-slate-600">{greeting.subtitle}</p>

      <label className="mt-10 w-full max-w-sm text-left">
        <span className="mb-2 block text-sm font-medium text-slate-700">Who are you greeting?</span>
        <input
          data-walkthrough="name-input"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="World"
          className="w-full rounded-xl border-2 border-slate-200 bg-white px-4 py-3 text-lg text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-fuchsia-500 focus:ring-4 focus:ring-fuchsia-200"
        />
      </label>
      <button
        type="button"
        data-walkthrough="reset"
        onClick={() => setName('')}
        className="mt-4 rounded-full bg-blue-600 px-5 py-2 text-sm font-semibold text-white shadow-md shadow-blue-300/60 transition hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
      >
        Reset to World
      </button>
    </div>
  )
}
