import type { ReactNode } from 'react'
import { Loader2, Lock } from 'lucide-react'
import type { Me } from '@/hooks/useMe'

export function AdminOnly({
  me,
  loaded,
  children,
}: {
  me: Me | null
  loaded: boolean
  children: ReactNode
}) {
  if (!loaded)
    return (
      <div className="flex items-center justify-center gap-2 py-20 text-ink-soft">
        <Loader2 className="size-4 animate-spin" /> Checking access…
      </div>
    )
  if (!me?.is_admin)
    return (
      <main className="mx-auto max-w-xl px-5 py-16">
        <div className="rounded-2xl border border-line bg-sheet p-8">
          <Lock className="size-6 text-cobalt" />
          <h1 className="mt-3 text-lg font-bold">Admins only</h1>
          <p className="mt-2 text-ink-soft">
            The product catalog reads live Salesforce data through a shared connector account, so
            access is limited to app admins for now. Ask an admin to change your role if you need
            it.
          </p>
        </div>
      </main>
    )
  return <>{children}</>
}
