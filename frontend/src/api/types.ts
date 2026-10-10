export type DocumentStatus = 'uploaded' | 'processing' | 'ready' | 'failed'
export type ExtractionMethod = 'native' | 'ocr'

export interface HealthResponse {
  status: string
}

export interface DocumentResponse {
  id: string
  project_id: string
  filename: string
  file_type: string
  size_bytes: number
  page_count: number | null
  status: DocumentStatus
  created_at: string
}

export interface DocumentSection {
  id: string
  position: number
  text: string
  page_number: number | null
  extraction_method: ExtractionMethod
  confidence: number | null
}

export interface QuestionRequest {
  project_id: string
  thread_id: string
  question: string
  document_id?: string
  retrieval_limit?: number
}

export interface QuestionSource {
  chunk_id: string
  document_id: string
  text: string
  page_number: number | null
  score: number
}

export interface QuestionResponse {
  answer: string
  sources: QuestionSource[]
  author: AuthUser
}

export interface AuthUser {
  id: string
  email: string
  display_name: string
  member_id: string
}

export interface ConversationTurnRecord {
  id: string
  project_id: string
  thread_id: string
  question: string
  answer: string
  created_at: string
  author: Omit<AuthUser, 'member_id'>
}

export interface RagEvidence {
  sources: QuestionSource[]
}

export interface SemanticSearchRequest {
  project_id: string
  query: string
  document_id?: string
  limit?: number
}

export type SemanticSearchResult = QuestionSource

export interface KnowledgeConcept {
  id: string
  label: string
  description: string
  source_chunk_ids: string[]
}

export interface KnowledgeRelation {
  source_id: string
  target_id: string
  label: string
  source_chunk_ids: string[]
}

export interface KnowledgeGraph {
  concepts: KnowledgeConcept[]
  relations: KnowledgeRelation[]
}

export interface ConversationTurn {
  question: string
  answer: string
}

export interface Project {
  id: string
  name: string
  created_at: string
  updated_at: string
}

export interface ProjectMember {
  id: string
  member_id: string
  display_name: string | null
  role: 'owner' | 'editor' | 'viewer'
  created_at: string
}

export interface SessionIdentity {
  member_id: string
}

export interface InsightTakeaway {
  title: string
  explanation: string
  source_turn_numbers: number[]
}

export interface InsightAction {
  rank: number
  title: string
  rationale: string
  priority: 'high' | 'medium' | 'low'
  kind: 'explicit' | 'recommendation' | 'open_question'
  source_turn_numbers: number[]
}

export interface ConversationInsights {
  id: string
  project_id: string
  thread_id: string
  takeaways: InsightTakeaway[]
  actions: InsightAction[]
  created_at: string
}
