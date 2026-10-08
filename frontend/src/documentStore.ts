import { useSyncExternalStore } from 'react'
import { api, ApiError } from './api/client'
import type { DocumentResponse } from './api/types'

interface DocumentState {
  documents: DocumentResponse[]
  activeDocumentId: string | null
  loading: boolean
  error: string | null
}

let state: DocumentState = {
  documents: [],
  activeDocumentId: window.localStorage.getItem('intellect-active-document'),
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
  select(documentId: string | null) {
    if (documentId) window.localStorage.setItem('intellect-active-document', documentId)
    else window.localStorage.removeItem('intellect-active-document')
    update({ activeDocumentId: documentId })
  },
  async load() {
    update({ loading: true, error: null })
    try {
      const documents = await api.documents.list()
      const activeExists = documents.some((item) => item.id === state.activeDocumentId)
      const activeDocumentId = activeExists ? state.activeDocumentId : documents[0]?.id || null
      if (activeDocumentId) window.localStorage.setItem('intellect-active-document', activeDocumentId)
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
    const pending = state.documents.filter((item) => item.status === 'uploaded' || item.status === 'processing')
    if (pending.length === 0) return
    try {
      const refreshed = await Promise.all(pending.map((item) => api.documents.get(item.id)))
      const byId = new Map(refreshed.map((item) => [item.id, item]))
      update({ documents: state.documents.map((item) => byId.get(item.id) || item) })
    } catch {
      // A regular list refresh exposes persistent API errors without noisy polling errors.
    }
  },
  async upload(file: File) {
    update({ error: null })
    const document = await api.documents.upload(file)
    window.localStorage.setItem('intellect-active-document', document.id)
    update({
      documents: [document, ...state.documents.filter((item) => item.id !== document.id)],
      activeDocumentId: document.id,
    })
    return document
  },
  async remove(documentId: string) {
    update({ error: null })
    try {
      await api.documents.remove(documentId)
      const documents = state.documents.filter((item) => item.id !== documentId)
      const activeDocumentId = state.activeDocumentId === documentId ? documents[0]?.id || null : state.activeDocumentId
      this.select(activeDocumentId)
      update({ documents, activeDocumentId })
    } catch (error) {
      update({ error: messageFrom(error) })
    }
  },
  async waitUntilReady(documentId: string, timeoutMs = 120_000) {
    const startedAt = Date.now()
    while (Date.now() - startedAt < timeoutMs) {
      const document = await api.documents.get(documentId)
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
