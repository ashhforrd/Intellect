import { useSyncExternalStore } from 'react'
import { api, ApiError } from './api/client'
import type { AuthUser } from './api/types'

type AuthState = {
  user: AuthUser | null
  loading: boolean
  ready: boolean
  error: string | null
}

let state: AuthState = { user: null, loading: false, ready: false, error: null }
const listeners = new Set<() => void>()

function update(patch: Partial<AuthState>) {
  state = { ...state, ...patch }
  listeners.forEach((listener) => listener())
}

export const authStore = {
  getSnapshot: () => state,
  subscribe(listener: () => void) {
    listeners.add(listener)
    return () => listeners.delete(listener)
  },
  async load() {
    update({ loading: true, error: null })
    try {
      const user = await api.auth.me()
      update({ user, loading: false, ready: true })
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        update({ user: null, loading: false, ready: true })
        return
      }
      update({ loading: false, ready: true, error: error instanceof Error ? error.message : 'Unable to check your session.' })
    }
  },
  async login(email: string, password: string) {
    update({ loading: true, error: null })
    try {
      const user = await api.auth.login(email, password)
      update({ user, loading: false, ready: true })
      return true
    } catch (error) {
      update({ loading: false, error: error instanceof Error ? error.message : 'Unable to sign in.' })
      return false
    }
  },
  async logout() {
    try { await api.auth.logout() } finally {
      window.localStorage.removeItem('intellect-active-project')
      update({ user: null, error: null, ready: true })
    }
  },
}

export function useAuth() {
  return useSyncExternalStore(authStore.subscribe, authStore.getSnapshot)
}
