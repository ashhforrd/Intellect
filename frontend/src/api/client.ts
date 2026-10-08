import { apiBaseUrl } from './config'
import type {
  DocumentResponse,
  ConversationTurn,
  DocumentSection,
  HealthResponse,
  KnowledgeGraph,
  QuestionRequest,
  QuestionResponse,
  SemanticSearchRequest,
  SemanticSearchResult,
} from './types'

interface ErrorBody {
  detail?: string
}

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  let response: Response
  try {
    response = await fetch(`${apiBaseUrl}${path}`, { ...options, headers })
  } catch {
    throw new ApiError('Cannot connect to the document intelligence API.', 0)
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null) as ErrorBody | null
    throw new ApiError(body?.detail || `Request failed with status ${response.status}.`, response.status)
  }

  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

async function requestBlob(path: string): Promise<Blob> {
  const response = await fetch(`${apiBaseUrl}${path}`)
  if (!response.ok) throw new ApiError(`Request failed with status ${response.status}.`, response.status)
  return response.blob()
}

export const api = {
  health: () => request<HealthResponse>('/health'),

  documents: {
    list: (limit = 50, offset = 0) =>
      request<DocumentResponse[]>(`/documents?limit=${limit}&offset=${offset}`),
    get: (documentId: string) => request<DocumentResponse>(`/documents/${documentId}`),
    upload: (file: File) => {
      const form = new FormData()
      form.append('file', file)
      return request<DocumentResponse>('/documents', { method: 'POST', body: form })
    },
    remove: (documentId: string) =>
      request<void>(`/documents/${documentId}`, { method: 'DELETE' }),
    content: (documentId: string) => requestBlob(`/documents/${documentId}/content`),
    sections: (documentId: string) =>
      request<DocumentSection[]>(`/documents/${documentId}/sections`),
  },

  questions: {
    ask: (payload: QuestionRequest, signal?: AbortSignal) =>
      request<QuestionResponse>('/questions', {
        method: 'POST',
        body: JSON.stringify(payload),
        signal,
      }),
  },

  search: (payload: SemanticSearchRequest, signal?: AbortSignal) =>
    request<SemanticSearchResult[]>('/search', {
      method: 'POST',
      body: JSON.stringify(payload),
      signal,
    }),

  knowledgeGraph: {
    get: (documentId: string, signal?: AbortSignal) =>
      request<KnowledgeGraph>(`/documents/${documentId}/knowledge-graph`, { signal }),
    generate: (documentId: string, signal?: AbortSignal) =>
      request<KnowledgeGraph>(`/documents/${documentId}/knowledge-graph`, {
        method: 'POST',
        signal,
      }),
    fromConversation: (turns: ConversationTurn[], signal?: AbortSignal) =>
      request<KnowledgeGraph>('/knowledge/conversation-graph', {
        method: 'POST',
        body: JSON.stringify({ turns }),
        signal,
      }),
  },
}
