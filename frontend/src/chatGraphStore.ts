import { useSyncExternalStore } from 'react'
import type { KnowledgeGraph } from './api/types'

export type ChatGraphNode = {
  id: string
  label: string
  detail: string
  kind: 'concept'
}

export type ChatGraphEdge = {
  id: string
  source: string
  target: string
  label?: string
}

type GraphData = { nodes: ChatGraphNode[]; edges: ChatGraphEdge[] }

const storageKey = 'intellect-conversation-graphs-v3'
const emptyGraph: GraphData = { nodes: [], edges: [] }
let graphs: Record<string, GraphData> = loadGraphs()
const listeners = new Set<() => void>()

function loadGraphs(): Record<string, GraphData> {
  try { return JSON.parse(window.localStorage.getItem(storageKey) || '{}') }
  catch { return {} }
}

function emit() {
  window.localStorage.setItem(storageKey, JSON.stringify(graphs))
  listeners.forEach((listener) => listener())
}

export const chatGraphStore = {
  replace(threadId: string, graph: KnowledgeGraph) {
    const conceptIds = new Set(graph.concepts.map((concept) => concept.id))
    graphs = {
      ...graphs,
      [threadId]: {
        nodes: graph.concepts.map((concept) => ({
          id: concept.id,
          label: concept.label,
          detail: concept.description,
          kind: 'concept' as const,
        })),
        edges: graph.relations
          .filter((relation) => conceptIds.has(relation.source_id) && conceptIds.has(relation.target_id))
          .map((relation, index) => ({
            id: `${relation.source_id}-${relation.target_id}-${index}`,
            source: relation.source_id,
            target: relation.target_id,
            label: relation.label,
          })),
      },
    }
    emit()
  },
  get(threadId: string) { return graphs[threadId] || emptyGraph },
  clear(threadId: string) { graphs = { ...graphs, [threadId]: emptyGraph }; emit() },
  subscribe(listener: () => void) { listeners.add(listener); return () => listeners.delete(listener) },
}

export function useChatGraph(threadId: string) {
  return useSyncExternalStore(chatGraphStore.subscribe, () => chatGraphStore.get(threadId))
}
