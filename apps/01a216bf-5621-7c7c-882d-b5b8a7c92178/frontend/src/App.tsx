import { Toaster } from 'sonner'
import GreetingCard from './components/GreetingCard'

export default function App() {
  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-white px-6 py-16 text-slate-900">
      <div className="pointer-events-none absolute -left-24 -top-24 h-96 w-96 rounded-full bg-sky-300/50 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-32 -right-24 h-[28rem] w-[28rem] rounded-full bg-orange-300/50 blur-3xl" />
      <div className="pointer-events-none absolute right-1/4 top-10 h-64 w-64 rounded-full bg-fuchsia-300/40 blur-3xl" />
      <GreetingCard />
      <Toaster position="top-center" richColors />
    </main>
  )
}
