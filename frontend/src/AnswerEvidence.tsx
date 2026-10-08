import { useState } from 'react'
import { type DataMessagePartComponent, type DataMessagePartProps } from '@assistant-ui/react'
import { BookOpen, ChevronDown, FileSearch, Lightbulb } from 'lucide-react'
import type { RagEvidence } from './api/types'
import { useDocuments } from './documentStore'

export const AnswerEvidence: DataMessagePartComponent<RagEvidence> = ({ data }: DataMessagePartProps<RagEvidence>) => {
  const evidence = data as RagEvidence
  const { documents } = useDocuments()
  const [showReasoning, setShowReasoning] = useState(false)
  const [showChunks, setShowChunks] = useState(false)
  const [showSources, setShowSources] = useState(false)
  const [openSource, setOpenSource] = useState<number | null>(null)

  return <div className="answer-evidence">
    {evidence.sources.length > 0 && <section className="answer-sources" aria-label="Sources used for this answer">
      <button className="evidence-toggle" type="button" onClick={() => setShowSources(!showSources)}><BookOpen size={13} /><span>Sources</span><ChevronDown className={showSources ? 'rotated' : ''} size={13} /></button>
      {showSources && <div className="source-list">
      {evidence.sources.map((source, index) => <article className="source-card" key={source.chunk_id}>
        <button type="button" onClick={() => setOpenSource(openSource === index ? null : index)}>
          <span className="source-number">{index + 1}</span>
          <span><strong>{documents.find((item) => item.id === source.document_id)?.filename || 'Document source'}</strong><small>Page {source.page_number ?? '—'} · score {source.score.toFixed(2)}</small></span>
          <ChevronDown className={openSource === index ? 'rotated' : undefined} size={14} />
        </button>
        {openSource === index && <p>{source.text}</p>}
      </article>)}
      </div>}
    </section>}

    <button className="evidence-toggle" type="button" onClick={() => setShowReasoning(!showReasoning)}>
      <Lightbulb size={13} /><span>Answer construction</span><ChevronDown className={showReasoning ? 'rotated' : ''} size={13} />
    </button>
    {showReasoning && <div className="reasoning-summary">
      <span>Retrieved document passages</span><i />
      <span>Filtered by relevance</span><i />
      <span>Generated a grounded answer</span>
      <p>This is a high-level process summary, not hidden model reasoning.</p>
    </div>}

    <button className="evidence-toggle" type="button" onClick={() => setShowChunks(!showChunks)}>
      <FileSearch size={13} /><span>Inspect retrieval chunks</span><ChevronDown className={showChunks ? 'rotated' : ''} size={13} />
    </button>
    {showChunks && <div className="retrieval-chunks">
      {evidence.sources.map((source) => <article key={source.chunk_id}>
        <header><span>Page {source.page_number ?? '—'}</span><em>{source.score.toFixed(2)} match</em></header>
        <p>{source.text}</p>
      </article>)}
      {evidence.sources.length === 0 && <p className="empty-evidence">No relevant chunks passed the relevance threshold.</p>}
    </div>}

  </div>
}
