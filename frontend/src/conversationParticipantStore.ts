import { useSyncExternalStore } from 'react'
import type { ConversationParticipant } from './api/types'
import { useAuth } from './authStore'

type ParticipantMap = Record<string, readonly ConversationParticipant[]>
let participants: ParticipantMap = {}
const listeners = new Set<() => void>()
const empty: readonly ConversationParticipant[] = []
const key = (accountId: string, projectId: string, threadId: string) =>
  JSON.stringify([accountId, projectId, threadId])

function update(next: ParticipantMap) {
  participants = next
  listeners.forEach(listener => listener())
}

export const conversationParticipantStore = {
  set(accountId: string, projectId: string, threadId: string, users: readonly ConversationParticipant[]) {
    const unique = [...new Map(users.map(user => [user.id, user])).values()]
    update({ ...participants, [key(accountId, projectId, threadId)]: unique })
  },
  add(accountId: string, projectId: string, threadId: string, user: ConversationParticipant) {
    this.set(accountId, projectId, threadId, [...(participants[key(accountId, projectId, threadId)] || empty), user])
  },
  remove(accountId: string, projectId: string, threadId: string) {
    const next = { ...participants }
    delete next[key(accountId, projectId, threadId)]
    update(next)
  },
  getSnapshot: () => participants,
  subscribe(listener: () => void) {
    listeners.add(listener)
    return () => listeners.delete(listener)
  },
}

export function useConversationParticipants(projectId: string, threadId: string) {
  const { user } = useAuth()
  const entries = useSyncExternalStore(conversationParticipantStore.subscribe, conversationParticipantStore.getSnapshot)
  return user ? entries[key(user.id, projectId, threadId)] || empty : empty
}
