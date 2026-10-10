import { apiBaseUrl } from './config'
import type {
  DocumentResponse,
  ConversationTurn,
  DocumentSection,
  HealthResponse,
  KnowledgeGraph,
  Project,
  ProjectMember,
  SessionIdentity,
  ConversationInsights,
  AuthUser,
  ConversationTurnRecord,
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
    response = await fetch(`${apiBaseUrl}${path}`, { ...options, headers, credentials: 'include' })
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
  const response = await fetch(`${apiBaseUrl}${path}`, { credentials: 'include' })
  if (!response.ok) throw new ApiError(`Request failed with status ${response.status}.`, response.status)
  return response.blob()
}

export const api = {
  health: () => request<HealthResponse>('/health'),
  session: () => request<SessionIdentity>('/session'),

  auth: {
    login: (email: string, password: string) => request<AuthUser>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
    me: () => request<AuthUser>('/auth/me'),
    logout: () => request<void>('/auth/logout', { method: 'POST' }),
  },

  projects: {
    list: () => request<Project[]>('/projects'),
    create: (name: string) => request<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify({ name }),
    }),
    rename: (projectId: string, name: string) => request<Project>(`/projects/${projectId}`, {
      method: 'PATCH',
      body: JSON.stringify({ name }),
    }),
    remove: (projectId: string) => request<void>(`/projects/${projectId}`, { method: 'DELETE' }),
    members: (projectId: string) => request<ProjectMember[]>(`/projects/${projectId}/members`),
    addMember: (
      projectId: string,
      payload: { member_id: string; display_name?: string; role: 'editor' | 'viewer' },
    ) => request<ProjectMember>(`/projects/${projectId}/members`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
    removeMember: (projectId: string, memberId: string) =>
      request<void>(`/projects/${projectId}/members/${encodeURIComponent(memberId)}`, {
        method: 'DELETE',
      }),
  },

  documents: {
    list: (projectId: string, limit = 50, offset = 0) =>
      request<DocumentResponse[]>(`/documents?project_id=${projectId}&limit=${limit}&offset=${offset}`),
    get: (projectId: string, documentId: string) =>
      request<DocumentResponse>(`/documents/${documentId}?project_id=${projectId}`),
    upload: (projectId: string, file: File) => {
      const form = new FormData()
      form.append('file', file)
      return request<DocumentResponse>(`/documents?project_id=${projectId}`, { method: 'POST', body: form })
    },
    remove: (projectId: string, documentId: string) =>
      request<void>(`/documents/${documentId}?project_id=${projectId}`, { method: 'DELETE' }),
    content: (projectId: string, documentId: string) =>
      requestBlob(`/documents/${documentId}/content?project_id=${projectId}`),
    sections: (projectId: string, documentId: string) =>
      request<DocumentSection[]>(`/documents/${documentId}/sections?project_id=${projectId}`),
  },

  questions: {
    ask: (payload: QuestionRequest, signal?: AbortSignal) =>
      request<QuestionResponse>('/questions', {
        method: 'POST',
        body: JSON.stringify(payload),
        signal,
      }),
    conversation: (projectId: string, threadId: string) =>
      request<ConversationTurnRecord[]>(`/questions/conversations/${projectId}/${encodeURIComponent(threadId)}`),
  },

  search: (payload: SemanticSearchRequest, signal?: AbortSignal) =>
    request<SemanticSearchResult[]>('/search', {
      method: 'POST',
      body: JSON.stringify(payload),
      signal,
    }),

  knowledgeGraph: {
    get: (projectId: string, documentId: string, signal?: AbortSignal) =>
      request<KnowledgeGraph>(`/documents/${documentId}/knowledge-graph?project_id=${projectId}`, { signal }),
    generate: (projectId: string, documentId: string, signal?: AbortSignal) =>
      request<KnowledgeGraph>(`/documents/${documentId}/knowledge-graph?project_id=${projectId}`, {
        method: 'POST',
        signal,
      }),
    fromConversation: (projectId: string, turns: ConversationTurn[], signal?: AbortSignal) =>
      request<KnowledgeGraph>('/knowledge/conversation-graph', {
        method: 'POST',
        body: JSON.stringify({ project_id: projectId, turns }),
        signal,
      }),
  },

  insights: {
    get: (projectId: string, threadId: string) =>
      request<ConversationInsights | null>(`/insights/conversation/${projectId}/${encodeURIComponent(threadId)}`),
    generate: (projectId: string, threadId: string, turns: ConversationTurn[]) =>
      request<ConversationInsights>('/insights/conversation', {
        method: 'POST',
        body: JSON.stringify({ project_id: projectId, thread_id: threadId, turns }),
      }),
  },
}
