import { useSyncExternalStore } from 'react'
import { api, ApiError } from './api/client'
import type { DocumentResponse } from './api/types'

interface DocumentState {
  projectId: string | null
  documents: DocumentResponse[]
  activeDocumentId: string | null
  loading: boolean
  error: string | null
}

let state: DocumentState = {
  projectId: null,
  documents: [],
  activeDocumentId: null,
  loading: false,
  error: null,
}

const listeners = new Set<() => void>()

function update(patch: Partial<DocumentState>) {
  state = { ...state, ...patch }
  listeners.forEach((listener) => listener())
}

function messageFrom(error: unknown) {
  return error instanceof ApiError ? error.message : 'An unexpected error occurred.'
}

export const documentStore = {
  getSnapshot: () => state,
  subscribe(listener: () => void) {
    listeners.add(listener)
    return () => listeners.delete(listener)
  },
  async setProject(projectId: string) {
    const activeDocumentId = window.localStorage.getItem(`intellect-active-document:${projectId}`)
    update({ projectId, documents: [], activeDocumentId, error: null })
    await this.load()
  },
  select(documentId: string | null) {
    if (!state.projectId) return
    const key = `intellect-active-document:${state.projectId}`
    if (documentId) window.localStorage.setItem(key, documentId)
    else window.localStorage.removeItem(key)
    update({ activeDocumentId: documentId })
  },
  async load() {
    if (!state.projectId) return
    update({ loading: true, error: null })
    try {
      const documents = await api.documents.list(state.projectId)
      const activeExists = documents.some((item) => item.id === state.activeDocumentId)
      const activeDocumentId = activeExists ? state.activeDocumentId : documents[0]?.id || null
      if (activeDocumentId) window.localStorage.setItem(`intellect-active-document:${state.projectId}`, activeDocumentId)
      update({
        documents,
        activeDocumentId,
        loading: false,
      })
    } catch (error) {
      update({ loading: false, error: messageFrom(error) })
    }
  },
  async refreshProcessing() {
    if (!state.projectId) return
    const pending = state.documents.filter((item) => item.status === 'uploaded' || item.status === 'processing')
    if (pending.length === 0) return
    try {
      const refreshed = await Promise.all(pending.map((item) => api.documents.get(state.projectId!, item.id)))
      const byId = new Map(refreshed.map((item) => [item.id, item]))
      update({ documents: state.documents.map((item) => byId.get(item.id) || item) })
    } catch {
      // A regular list refresh exposes persistent API errors without noisy polling errors.
    }
  },
  async upload(file: File) {
    if (!state.projectId) throw new Error('Select a project before uploading documents.')
    update({ error: null })
    const document = await api.documents.upload(state.projectId, file)
    window.localStorage.setItem(`intellect-active-document:${state.projectId}`, document.id)
    update({
      documents: [document, ...state.documents.filter((item) => item.id !== document.id)],
      activeDocumentId: document.id,
    })
    return document
  },
  async remove(documentId: string) {
    if (!state.projectId) return
    update({ error: null })
    try {
      await api.documents.remove(state.projectId, documentId)
      const documents = state.documents.filter((item) => item.id !== documentId)
      const activeDocumentId = state.activeDocumentId === documentId ? documents[0]?.id || null : state.activeDocumentId
      this.select(activeDocumentId)
      update({ documents, activeDocumentId })
    } catch (error) {
      update({ error: messageFrom(error) })
    }
  },
  async waitUntilReady(documentId: string, timeoutMs = 120_000) {
    if (!state.projectId) throw new Error('Select a project before processing documents.')
    const startedAt = Date.now()
    while (Date.now() - startedAt < timeoutMs) {
      const document = await api.documents.get(state.projectId, documentId)
      update({
        documents: state.documents.map((item) => item.id === document.id ? document : item),
      })
      if (document.status === 'ready') return document
      if (document.status === 'failed') throw new Error('Document processing failed.')
      await new Promise((resolve) => window.setTimeout(resolve, 2000))
    }
    throw new Error('Document processing is taking longer than expected. Keep the worker running and retry.')
  },
}

export function useDocuments() {
  return useSyncExternalStore(documentStore.subscribe, documentStore.getSnapshot)
}
