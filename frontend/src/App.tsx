import { useEffect, useRef, useState } from 'react'
import * as AlertDialog from '@radix-ui/react-alert-dialog'
import {
  AuiIf,
  AttachmentPrimitive,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadListItemPrimitive,
  ThreadListPrimitive,
  ThreadPrimitive,
  useAui,
  useAuiState,
} from '@assistant-ui/react'
import {
  ArrowUp, FileText, GitBranch, LoaderCircle, Menu,
  Eye, MoreHorizontal, PanelRightClose, Paperclip, Plus, RefreshCw,
  Search, Square, Trash2, X,
} from 'lucide-react'
import { AnswerEvidence } from './AnswerEvidence'
import { AssistantRuntimeProvider } from './AssistantRuntimeProvider'
import { ChatGraph } from './ChatGraph'
import { MarkdownAnswer } from './MarkdownAnswer'
import { OwlMascot } from './OwlMascot'
import { api } from './api/client'
import { chatGraphStore, useChatGraph } from './chatGraphStore'
import { documentStore, useDocuments } from './documentStore'
import './App.css'
import './assistant.css'
import './focus.css'
import './theme-dark.css'
import './attachments.css'
import './markdown.css'
import './evidence.css'
import './integration.css'
import './monochrome.css'

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [graphOpen, setGraphOpen] = useState(false)

  useEffect(() => {
    void documentStore.load()
    const polling = window.setInterval(() => void documentStore.refreshProcessing(), 3000)
    return () => window.clearInterval(polling)
  }, [])

  return <AssistantRuntimeProvider>
    <div className={`app ${sidebarOpen ? '' : 'sidebar-closed'} ${graphOpen ? 'graph-open' : ''}`}>
      <Sidebar onClose={() => setSidebarOpen(false)} />
      <main>
        <AppHeader
          sidebarOpen={sidebarOpen}
          graphOpen={graphOpen}
          onOpenSidebar={() => setSidebarOpen(true)}
          onToggleGraph={() => setGraphOpen(!graphOpen)}
        />
        <ChatThread />
      </main>
      <KnowledgeGraphPanel open={graphOpen} onClose={() => setGraphOpen(false)} />
      {sidebarOpen && <button className="mobile-overlay" aria-label="Close sidebar" onClick={() => setSidebarOpen(false)} />}
    </div>
  </AssistantRuntimeProvider>
}

function Sidebar({ onClose }: { onClose: () => void }) {
  const { documents, activeDocumentId, loading, error } = useDocuments()
  const [searchOpen, setSearchOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [documentToDelete, setDocumentToDelete] = useState<{ id: string; filename: string } | null>(null)
  const aui = useAui()
  const normalizedSearch = search.trim().toLowerCase()
  const visibleDocuments = documents.filter((document) => document.filename.toLowerCase().includes(normalizedSearch))

  async function startNewChat() {
    await aui.threads.switchToNewThread()
  }

  async function previewDocument(documentId: string) {
    const previewTab = window.open('', '_blank')
    try {
      const blob = await api.documents.content(documentId)
      const url = URL.createObjectURL(blob)
      if (previewTab) previewTab.location.href = url
      else window.open(url, '_blank')
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000)
    } catch {
      previewTab?.close()
    }
  }

  return <aside className="sidebar">
    <div className="sidebar-top"><button className="icon-button mobile-menu" onClick={onClose}><Menu size={18} /></button><div className="brand"><span><OwlMascot size={19} /></span>intellect</div><button className="icon-button" aria-label="Search" onClick={() => setSearchOpen(!searchOpen)}><Search size={17} /></button></div>
    {searchOpen && <div className="sidebar-search"><Search size={15} /><input autoFocus value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search chats and documents" /><button onClick={() => { setSearch(''); setSearchOpen(false) }}><X size={14} /></button></div>}
    <ThreadListPrimitive.Root>
      <button className="new-chat" type="button" onClick={() => void startNewChat()}><Plus size={16} />New chat</button>
      <div className="history"><p>CONVERSATIONS</p><ThreadListPrimitive.Items>{({ threadListItem }) => !normalizedSearch || threadListItem.title?.toLowerCase().includes(normalizedSearch) ? <ThreadListItem /> : null}</ThreadListPrimitive.Items></div>
    </ThreadListPrimitive.Root>
    <div className="document-list">
      <div className="document-list-title"><p>DOCUMENTS</p><button onClick={() => void documentStore.load()} aria-label="Refresh documents"><RefreshCw size={12} /></button></div>
      {loading && <span className="document-note"><LoaderCircle className="spin" size={11} />Loading documents</span>}
      {error && <span className="document-error">{error}</span>}
      {!loading && documents.length === 0 && <span className="document-note">Attach a document to begin.</span>}
      {visibleDocuments.map((document) => <div className={document.id === activeDocumentId ? 'document-row active' : 'document-row'} key={document.id}>
        <button className="document-item" onClick={() => documentStore.select(document.id)}><FileText size={15} /><span><b>{document.filename}</b><small>{document.status}</small></span><i className={`status-dot ${document.status}`} /></button>
        <div className="document-actions"><button title="Preview document" aria-label={`Preview ${document.filename}`} onClick={() => void previewDocument(document.id)}><Eye size={14} /></button><button title="Delete document" aria-label={`Delete ${document.filename}`} onClick={() => setDocumentToDelete({ id: document.id, filename: document.filename })}><Trash2 size={14} /></button></div>
      </div>)}
    </div>
    <div className="sidebar-bottom"><span className="avatar">AH</span><div><b>Atqiya Haydar</b><small>Personal workspace</small></div><MoreHorizontal size={16} /></div>
    <ConfirmDeleteDialog
      open={documentToDelete !== null}
      title="Delete document?"
      description={documentToDelete ? `${documentToDelete.filename} and its processed data will be permanently deleted.` : ''}
      onOpenChange={(open) => { if (!open) setDocumentToDelete(null) }}
      onConfirm={() => { if (documentToDelete) void documentStore.remove(documentToDelete.id); setDocumentToDelete(null) }}
    />
  </aside>
}

function ThreadListItem() {
  const aui = useAui()
  const threadId = useAuiState((state) => state.threadListItem.id)
  const title = useAuiState((state) => state.threadListItem.title) || 'this conversation'
  const [confirmOpen, setConfirmOpen] = useState(false)

  return <ThreadListItemPrimitive.Root className="thread-list-item">
    <ThreadListItemPrimitive.Trigger><ThreadListItemPrimitive.Title fallback="New conversation" /></ThreadListItemPrimitive.Trigger>
    <button className="delete-thread" type="button" aria-label={`Delete ${title}`} title="Delete conversation" onClick={(event) => { event.preventDefault(); event.stopPropagation(); setConfirmOpen(true) }}><Trash2 size={14} /></button>
    <ConfirmDeleteDialog
      open={confirmOpen}
      title="Delete conversation?"
      description={`“${title}” will be permanently removed from this browser.`}
      onOpenChange={setConfirmOpen}
      onConfirm={() => { chatGraphStore.clear(threadId); void aui.threads.item({ id: threadId }).delete(); setConfirmOpen(false) }}
    />
  </ThreadListItemPrimitive.Root>
}

function ConfirmDeleteDialog({ open, title, description, onOpenChange, onConfirm }: { open: boolean; title: string; description: string; onOpenChange: (open: boolean) => void; onConfirm: () => void }) {
  return <AlertDialog.Root open={open} onOpenChange={onOpenChange}>
    <AlertDialog.Portal>
      <AlertDialog.Overlay className="dialog-overlay" />
      <AlertDialog.Content className="dialog-content">
        <AlertDialog.Title className="dialog-title">{title}</AlertDialog.Title>
        <AlertDialog.Description className="dialog-description">{description}</AlertDialog.Description>
        <div className="dialog-actions">
          <AlertDialog.Cancel className="dialog-cancel">Cancel</AlertDialog.Cancel>
          <AlertDialog.Action className="dialog-delete" onClick={onConfirm}>Delete</AlertDialog.Action>
        </div>
      </AlertDialog.Content>
    </AlertDialog.Portal>
  </AlertDialog.Root>
}

function AppHeader({ sidebarOpen, graphOpen, onOpenSidebar, onToggleGraph }: { sidebarOpen: boolean; graphOpen: boolean; onOpenSidebar: () => void; onToggleGraph: () => void }) {
  const chatTitle = useAuiState((state) => state.threadListItem.title)
  return <header><div className="header-left">{!sidebarOpen && <button className="icon-button" onClick={onOpenSidebar}><Menu size={18} /></button>}<div className="workspace">{chatTitle || 'New conversation'}</div></div><button className={graphOpen ? 'graph-toggle active' : 'graph-toggle'} onClick={onToggleGraph}><GitBranch size={16} /><span>Knowledge graph</span></button></header>
}

function ChatThread() {
  return <ThreadPrimitive.Root className="aui-thread"><ThreadPrimitive.Viewport className="aui-viewport">
    <AuiIf condition={(state) => state.thread.isEmpty}><Welcome /></AuiIf>
    <ThreadPrimitive.Messages>{({ message }) => message.role === 'user' ? <UserMessage /> : <AssistantMessage />}</ThreadPrimitive.Messages>
    <AuiIf condition={(state) => state.thread.isRunning}><ProcessingStatus /></AuiIf>
    <ThreadPrimitive.ViewportFooter className="aui-footer"><Composer /><small>Intellect can make mistakes. Answers include citations when available.</small></ThreadPrimitive.ViewportFooter>
  </ThreadPrimitive.Viewport></ThreadPrimitive.Root>
}

function Welcome() {
  const suggestions = ['Summarize the key ideas', 'Connect related concepts', 'Create a study plan']
  return <div className="aui-welcome"><span><OwlMascot size={29} /></span><h1>What do you want to understand?</h1><p>Attach a document or select one from the sidebar, then ask a grounded question.</p><div>{suggestions.map((prompt) => <ThreadPrimitive.Suggestion key={prompt} prompt={prompt}>{prompt}</ThreadPrimitive.Suggestion>)}</div></div>
}

function UserMessage() {
  return <MessagePrimitive.Root className="message user-message"><div className="user-message-stack"><MessagePrimitive.Attachments>{() => <SentAttachment />}</MessagePrimitive.Attachments><div className="message-content"><MessagePrimitive.Parts /></div></div></MessagePrimitive.Root>
}

function AssistantMessage() {
  return <MessagePrimitive.Root className="message assistant-message"><span className="assistant-mark"><OwlMascot size={19} /></span><div className="message-content"><MessagePrimitive.Parts components={{ Text: MarkdownAnswer, data: { by_name: { 'rag-evidence': AnswerEvidence } } }} /></div></MessagePrimitive.Root>
}

function Composer() {
  return <ComposerPrimitive.AttachmentDropzone className="attachment-dropzone"><ComposerPrimitive.Root className="aui-composer"><DraftRestore /><ComposerPrimitive.Attachments>{() => <ComposerAttachment />}</ComposerPrimitive.Attachments><ComposerPrimitive.Input className="aui-input" placeholder="Ask anything about your documents..." rows={1} /><div className="composer-actions"><ComposerPrimitive.AddAttachment className="attach-button"><Paperclip size={16} /><span>Attach</span></ComposerPrimitive.AddAttachment><AuiIf condition={(state) => !state.thread.isRunning}><ComposerPrimitive.Send className="send"><ArrowUp size={17} /></ComposerPrimitive.Send></AuiIf><AuiIf condition={(state) => state.thread.isRunning}><ComposerPrimitive.Cancel className="send cancel"><Square size={12} /></ComposerPrimitive.Cancel></AuiIf></div></ComposerPrimitive.Root></ComposerPrimitive.AttachmentDropzone>
}

function DraftRestore() {
  const aui = useAui()
  const text = useAuiState((state) => state.composer.text)
  const ready = useRef(false)
  useEffect(() => {
    const draft = window.localStorage.getItem('intellect-composer-draft')
    if (draft) aui.composer.setText(draft)
    ready.current = true
  }, [aui])
  useEffect(() => {
    if (ready.current) window.localStorage.setItem('intellect-composer-draft', text)
  }, [text])
  return null
}

function ComposerAttachment() {
  return <AttachmentPrimitive.Root className="composer-attachment"><span className="attachment-icon"><FileText size={16} /></span><span className="attachment-copy"><span><AttachmentPrimitive.Name /></span><small>Uploading and processing</small></span><AttachmentPrimitive.Remove className="remove-attachment"><X size={13} /></AttachmentPrimitive.Remove></AttachmentPrimitive.Root>
}

function SentAttachment() {
  return <AttachmentPrimitive.Root className="sent-attachment"><FileText size={15} /><span><AttachmentPrimitive.Name /></span></AttachmentPrimitive.Root>
}

function ProcessingStatus() {
  return <div className="processing-status"><OwlMascot size={19} /><div><b>Preparing grounded answer</b><span><i />Retrieving chunks</span><span><i />Checking relevance</span><span><i />Generating response</span></div></div>
}

function KnowledgeGraphPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  const threadId = useAuiState((state) => state.threadListItem.id) || 'current'
  const messages = useAuiState((state) => state.thread.messages)
  const graph = useChatGraph(threadId)
  const [generating, setGenerating] = useState(false)
  const [graphError, setGraphError] = useState<string | null>(null)

  async function generateGraph() {
    const turns: Array<{ question: string; answer: string }> = []
    let question = ''
    for (const message of messages) {
      const text = message.content.filter((part) => part.type === 'text').map((part) => part.text).join(' ')
      if (message.role === 'user') question = text
      if (message.role === 'assistant' && question) {
        turns.push({ question, answer: text })
        question = ''
      }
    }
    if (turns.length === 0) return

    setGenerating(true)
    setGraphError(null)
    try {
      const generatedGraph = await api.knowledgeGraph.fromConversation(turns)
      chatGraphStore.replace(threadId, generatedGraph)
    } catch (error) {
      setGraphError(error instanceof Error ? error.message : 'Unable to generate conversation graph.')
    } finally {
      setGenerating(false)
    }
  }

  return <aside className="graph-panel" aria-hidden={!open}><div className="graph-header"><div><b>Knowledge graph</b><small>Current conversation</small></div><div className="graph-header-actions"><button className="refresh-graph" disabled={generating || messages.length === 0} onClick={() => void generateGraph()}><RefreshCw className={generating ? 'spin' : ''} size={14} />{graph.nodes.length ? 'Refresh' : 'Generate'}</button><button className="icon-button" onClick={onClose}><PanelRightClose size={18} /></button></div></div>
    <div className="graph-content">
      {graph.nodes.length > 0 && <ChatGraph nodes={graph.nodes} edges={graph.edges} />}
      {graph.nodes.length === 0 && <div className="graph-state"><span>{graphError || (generating ? 'Extracting meaningful concepts and relationships…' : 'Generate a study graph from this conversation.')}</span><button className="generate-graph" disabled={generating || messages.length === 0} onClick={() => void generateGraph()}>{generating ? 'Generating…' : 'Generate graph'}</button></div>}
    </div>
  </aside>
}
