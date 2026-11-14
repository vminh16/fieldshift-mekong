import { useSyncExternalStore } from 'react'

/**
 * Tiny hash router: `#/ruong/moi?lat=10&lng=105` → { path: '/ruong/moi', params }.
 * Hash routing keeps `vite preview` and static hosting working without server rewrites.
 */
export interface Route {
  path: string
  params: URLSearchParams
}

function read(): Route {
  const raw = window.location.hash.replace(/^#/, '') || '/'
  const [path, query = ''] = raw.split('?')
  return { path: path.replace(/\/+$/, '') || '/', params: new URLSearchParams(query) }
}

let current = read()
const listeners = new Set<() => void>()
window.addEventListener('hashchange', () => {
  current = read()
  listeners.forEach((l) => l())
})

export function useRoute(): Route {
  return useSyncExternalStore(
    (cb) => {
      listeners.add(cb)
      return () => listeners.delete(cb)
    },
    () => current,
  )
}

export function href(path: string, params?: Record<string, string | number | null | undefined>): string {
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(params ?? {})) if (v !== null && v !== undefined && v !== '') q.set(k, String(v))
  const s = q.toString()
  return `#${path}${s ? `?${s}` : ''}`
}

export function navigate(path: string, params?: Record<string, string | number | null | undefined>) {
  window.location.hash = href(path, params)
}
