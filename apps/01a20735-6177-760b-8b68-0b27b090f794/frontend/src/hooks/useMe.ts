import { useEffect, useState } from 'react'
import client from '@/api/client'
import type { components } from '@/api/schema'

export type Me = components['schemas']['MeResponse']

export function useMe() {
  const [me, setMe] = useState<Me | null>(null)
  const [loaded, setLoaded] = useState(false)
  useEffect(() => {
    let alive = true
    client
      .GET('/api/users/me')
      .then(({ data }) => {
        if (alive) setMe(data ?? null)
      })
      .catch(() => undefined)
      .finally(() => alive && setLoaded(true))
    return () => {
      alive = false
    }
  }, [])
  return { me, loaded }
}
