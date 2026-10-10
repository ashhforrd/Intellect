import { EvidenceToggle } from './components/EvidenceToggle'
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
  return <div className="mt-5 border-t border-neutral-800 pt-2">
    {evidence.sources.length > 0 && <section aria-label="Sources used for this answer" className="mt-4.25 border-t border-evidence-border pt-3.25">
      <EvidenceToggle open={showSources} onToggle={() => setShowSources(!showSources)}>
        <BookOpen size={13} />
        <span>Sources</span>
      </EvidenceToggle>
      {showSources && <div className="mb-2.5 grid gap-2">
        {evidence.sources.map((source, index) => <article key={source.chunk_id} className="mt-1.5 overflow-hidden rounded-lg border border-neutral-700 bg-neutral-900">
          <button
            type="button"
            aria-expanded={openSource === index}
            onClick={() => setOpenSource(openSource === index ? null : index)}
            className="grid w-full [grid-template-columns:1.25rem_1fr_auto] items-center gap-1.75 border-0 bg-transparent p-2 text-left text-xs text-evidence-text hover:bg-evidence-hover"
          >
            <span className="grid size-5 place-items-center rounded-md bg-neutral-200 text-2xs text-neutral-900">
              {index + 1}
            </span>
            <span>
              <strong className="block text-xs font-medium text-neutral-200">
                {documents.find((item) => item.id === source.document_id)?.filename || 'Document source'}
              </strong>
              <small className="mt-0.5 block text-2xs text-neutral-500">Page {source.page_number ?? '—'} · score {source.score.toFixed(2)}</small>
            </span>
            <ChevronDown
              className={`text-evidence-icon transition-transform duration-180 ${openSource === index ? 'rotate-180' : ''}`}
              aria-hidden="true"
              size={14}
            />
          </button>
          {openSource === index && <p className="m-0 pt-0 pr-2.5 pb-2.5 pl-8.75 text-xs leading-body text-neutral-300">
            {source.text}
          </p>}
        </article>)}
      </div>}
    </section>}

    <EvidenceToggle open={showReasoning} onToggle={() => setShowReasoning(!showReasoning)}>
      <Lightbulb size={13} />
      <span>Answer construction</span>
    </EvidenceToggle>
    {showReasoning && <div
      className="mt-0 mb-2 flex flex-wrap items-center gap-1.25 rounded-lg border border-neutral-700 bg-neutral-900 p-2.25 text-xs leading-body text-neutral-300"
    >
      <span>Retrieved document passages</span>
      <i className="h-px w-2.5 bg-neutral-600" />
      <span>Filtered by relevance</span>
      <i className="h-px w-2.5 bg-neutral-600" />
      <span>Generated a grounded answer</span>
      <p className="mt-1.25 mb-0 w-full text-2xs text-neutral-500">This is a high-level process summary, not hidden model reasoning.</p>
    </div>}

    <EvidenceToggle open={showChunks} onToggle={() => setShowChunks(!showChunks)}>
      <FileSearch size={13} />
      <span>Inspect retrieval chunks</span>
    </EvidenceToggle>
    {showChunks && <div className="mt-0 mb-2.5 grid gap-2">
      {evidence.sources.map((source) => <article key={source.chunk_id} className="rounded-lg border border-neutral-700 bg-neutral-900 p-2.25">
        <header className="flex h-17 items-center justify-between border-b border-neutral-800 bg-surface px-6 text-2xs text-neutral-500">
          <span>Page {source.page_number ?? '—'}</span>
          <em className="text-neutral-200 not-italic">{source.score.toFixed(2)} match</em>
        </header>
        <p className="mt-1.5 mb-0 text-xs leading-body text-neutral-300">
          {source.text}
        </p>
      </article>)}
      {evidence.sources.length === 0 && <p className="m-0 p-2.25 text-2xs text-evidence-muted">No relevant chunks passed the relevance threshold.</p>}
    </div>}

  </div>
}
