export type DocumentStatus = 'uploaded' | 'processing' | 'ready' | 'failed'
export type ExtractionMethod = 'native' | 'ocr'

export interface HealthResponse {
  status: string
}

export interface DocumentResponse {
  id: string
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
}

export interface RagEvidence {
  sources: QuestionSource[]
}

export interface SemanticSearchRequest {
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
