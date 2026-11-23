import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Loader2, Trash2, UserPlus } from 'lucide-react'
import client from '@/api/client'
import type { components } from '@/api/schema'
import { errorMessage } from '@/lib/notes'

type User = components['schemas']['UserResponse']
type Role = components['schemas']['UserCreate']['role']

export default function UsersPage() {
  const [users, setUsers] = useState<User[] | null>(null)
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [role, setRole] = useState<NonNullable<Role>>('admin')
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    const { data, error } = await client.GET('/api/users/')
    if (data) setUsers(data)
    else toast.error(errorMessage(error, 'Users could not be loaded.'))
  }, [])
  useEffect(() => {
    void load()
  }, [load])

  async function add(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    const { data, error } = await client.POST('/api/users/', { body: { email, name, role } })
    setBusy(false)
    if (!data) {
      toast.error(`User not added: ${errorMessage(error, 'unknown error')}`)
      return
    }
    toast.success('User added')
    setEmail('')
    setName('')
    void load()
  }

  async function changeRole(u: User, next: NonNullable<Role>) {
    const { data, error } = await client.PUT('/api/users/{user_id}', {
      params: { path: { user_id: u.id } },
      body: { role: next },
    })
    if (!data) toast.error(`Role not changed: ${errorMessage(error, 'unknown error')}`)
    else toast.success('Role changed')
    void load()
  }

  async function remove(u: User) {
    if (!window.confirm(`Remove ${u.email}? They keep notes access as a viewer.`)) return
    const { error, response } = await client.DELETE('/api/users/{user_id}', {
      params: { path: { user_id: u.id } },
    })
    if (!response.ok)
      toast.error(`User not removed: ${errorMessage(error, `HTTP ${response.status}`)}`)
    else toast.success('User removed')
    void load()
  }

  return (
    <main className="mx-auto max-w-4xl px-5 py-6 sm:px-8">
      <h1 className="text-2xl font-extrabold tracking-tight">Users</h1>
      <p className="mt-1 max-w-prose text-sm text-ink-soft">
        Everyone signed in can use notes. Admins can also open the product catalog and save product
        descriptions to Salesforce.
      </p>

      <form
        onSubmit={add}
        className="mt-5 flex flex-wrap items-end gap-2 rounded-2xl border border-line bg-sheet p-4"
      >
        <label className="min-w-56 flex-1 text-sm font-semibold">
          Email
          <input
            required
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-lg border border-line px-3 py-2 font-normal focus:border-cobalt focus:outline-none"
          />
        </label>
        <label className="min-w-40 flex-1 text-sm font-semibold">
          Name
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 w-full rounded-lg border border-line px-3 py-2 font-normal focus:border-cobalt focus:outline-none"
          />
        </label>
        <label className="text-sm font-semibold">
          Role
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as NonNullable<Role>)}
            className="mt-1 block rounded-lg border border-line px-3 py-2 font-normal"
          >
            <option value="admin">Admin</option>
            <option value="viewer">Viewer</option>
          </select>
        </label>
        <button
          type="submit"
          disabled={busy}
          className="inline-flex items-center gap-2 rounded-lg bg-cobalt px-4 py-2 text-sm font-semibold text-white hover:bg-cobalt-deep disabled:opacity-60"
        >
          <UserPlus className="size-4" /> Add user
        </button>
      </form>

      <div className="mt-5 overflow-hidden rounded-2xl border border-line bg-sheet">
        {!users ? (
          <p className="flex items-center gap-2 p-5 text-ink-soft">
            <Loader2 className="size-4 animate-spin" /> Loading…
          </p>
        ) : (
          <ul className="divide-y divide-line">
            {users.map((u) => (
              <li key={u.id} className="flex flex-wrap items-center gap-3 px-4 py-3">
                <div className="min-w-0 flex-1">
                  <p className="font-semibold">{u.name || u.email}</p>
                  {u.name && <p className="text-sm text-ink-soft">{u.email}</p>}
                </div>
                <select
                  aria-label={`Role for ${u.email}`}
                  value={u.role}
                  onChange={(e) => void changeRole(u, e.target.value as NonNullable<Role>)}
                  className="rounded-lg border border-line px-2 py-1.5 text-sm"
                >
                  <option value="admin">Admin</option>
                  <option value="viewer">Viewer</option>
                </select>
                <button
                  type="button"
                  aria-label={`Remove ${u.email}`}
                  onClick={() => void remove(u)}
                  className="rounded-lg p-2 text-ink-soft hover:bg-magenta-wash hover:text-magenta-deep"
                >
                  <Trash2 className="size-4" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  )
}
