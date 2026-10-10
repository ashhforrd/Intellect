import { useSyncExternalStore } from 'react'
import type { AuthUser } from './api/types'

const STORAGE_KEY = 'intellect-prompt-authors'
type PromptAuthor = Omit<AuthUser, 'member_id'>
type AuthorMap = Record<string, PromptAuthor>

function read(): AuthorMap {
  try {
    return JSON.parse(window.localStorage.getItem(STORAGE_KEY) || '{}') as AuthorMap
  } catch {
    return {}
  }
}

let authors = read()
const listeners = new Set<() => void>()

export const promptAuthorStore = {
  set(messageId: string, author: PromptAuthor) {
    authors = { ...authors, [messageId]: author }
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(authors))
    listeners.forEach((listener) => listener())
  },
  getSnapshot: () => authors,
  subscribe(listener: () => void) {
    listeners.add(listener)
    return () => listeners.delete(listener)
  },
}

export function usePromptAuthor(messageId: string) {
  const entries = useSyncExternalStore(
    promptAuthorStore.subscribe,
    promptAuthorStore.getSnapshot,
  )
  return entries[messageId] || null
}
