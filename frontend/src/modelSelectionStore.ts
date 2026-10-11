import { useSyncExternalStore } from 'react'
import { api } from './api/client'
import type { AnswerModelsResponse, ReasoningEffort } from './api/types'

type Selection = { model: string; reasoning_effort: ReasoningEffort }
type PickerState = {
  catalog: AnswerModelsResponse | null
  selection: Selection | null
  loading: boolean
  error: string | null
}

const initialState: PickerState = { catalog: null, selection: null, loading: true, error: null }
const states = new Map<string, PickerState>()
const listeners = new Set<() => void>()

function scope(accountId: string, projectId: string) {
  return `intellect-answer-model:${accountId}:${projectId}`
}

function update(key: string, patch: Partial<PickerState>) {
  states.set(key, { ...(states.get(key) ?? initialState), ...patch })
  listeners.forEach(listener => listener())
}

function restore(key: string, catalog: AnswerModelsResponse): Selection {
  let saved: Partial<Selection> | null = states.get(key)?.selection ?? null
  try {
    const stored = window.localStorage.getItem(key)
    if (stored) saved = JSON.parse(stored)
  } catch { /* Keep the in-memory selection or use defaults. */ }
  const model = catalog.models.find(item => item.id === saved?.model)
  if (model) {
    return {
      model: model.id,
      reasoning_effort: saved?.reasoning_effort && model.reasoning_efforts.includes(saved.reasoning_effort)
        ? saved.reasoning_effort : model.default_effort,
    }
  }
  return { model: catalog.default_model, reasoning_effort: catalog.default_effort }
}

export const modelSelectionStore = {
  getSnapshot(accountId: string, projectId: string) {
    return states.get(scope(accountId, projectId)) ?? initialState
  },
  subscribe(listener: () => void) {
    listeners.add(listener)
    return () => { listeners.delete(listener) }
  },
  async load(accountId: string, projectId: string, signal: AbortSignal) {
    const key = scope(accountId, projectId)
    update(key, { loading: true, error: null })
    try {
      const catalog = await api.questions.models(signal)
      if (signal.aborted) return
      update(key, { catalog, selection: restore(key, catalog), loading: false })
    } catch {
      if (signal.aborted) return
      update(key, { catalog: null, selection: null, loading: false, error: 'Model picker unavailable. Using the server default.' })
    }
  },
  select(accountId: string, projectId: string, modelId: string, effort?: ReasoningEffort) {
    const key = scope(accountId, projectId)
    const state = states.get(key)
    const model = state?.catalog?.models.find(item => item.id === modelId)
    if (!model) return
    const requestedEffort = effort ?? state?.selection?.reasoning_effort
    const selection: Selection = {
      model: model.id,
      reasoning_effort: requestedEffort && model.reasoning_efforts.includes(requestedEffort)
        ? requestedEffort : model.default_effort,
    }
    update(key, { selection })
    try { window.localStorage.setItem(key, JSON.stringify(selection)) } catch { /* Keep in memory. */ }
  },
}

export function useModelSelection(accountId: string, projectId: string) {
  return useSyncExternalStore(modelSelectionStore.subscribe, () => modelSelectionStore.getSnapshot(accountId, projectId))
}
