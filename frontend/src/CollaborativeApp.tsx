import { ui } from './ui'
import { useEffect, useRef, useState } from 'react'
import * as AlertDialog from '@radix-ui/react-alert-dialog'
import {
  AuiIf,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadListItemPrimitive,
  ThreadListPrimitive,
  ThreadPrimitive,
  useAui,
  useAuiState,
} from '@assistant-ui/react'
import {
  ArrowUp, Copy, Eye, FileText, Files, GitBranch, Lightbulb, LoaderCircle,
  LogOut, Menu, MessageSquare, PanelRightClose, Plus, Square,
  Trash2, Upload, UserPlus, Users, X,
} from 'lucide-react'
import { AnswerEvidence } from './AnswerEvidence'
import { AssistantRuntimeProvider } from './AssistantRuntimeProvider'
import { ChatGraph } from './ChatGraph'
import { MarkdownAnswer } from './MarkdownAnswer'
import { AppIcon, OwlMascot } from './OwlMascot'
import { api } from './api/client'
import type { ConversationInsights, ConversationTurn, ProjectMember } from './api/types'
import { chatGraphStore, useChatGraph } from './chatGraphStore'
import { documentStore, useDocuments } from './documentStore'
import { projectStore, useProjects } from './projectStore'
import { authStore, useAuth } from './authStore'
import { usePromptAuthor } from './promptAuthorStore'

type Page = 'chat' | 'documents'

export default function CollaborativeApp() {
  const { activeProjectId, loading, error } = useProjects()
  useEffect(() => { void projectStore.load() }, [])
  useEffect(() => {
    if (!activeProjectId) return
    void documentStore.setProject(activeProjectId)
    const polling = window.setInterval(() => void documentStore.refreshProcessing(), 3000)
    return () => window.clearInterval(polling)
  }, [activeProjectId])

  if (loading && !activeProjectId) return <FullPageState label="Opening your projects…" />
  if (error && !activeProjectId) return <FullPageState label={error} />
  if (!activeProjectId) return <FullPageState label="No project is available." />
  return <AssistantRuntimeProvider key={activeProjectId} projectId={activeProjectId}>
    <Workspace projectId={activeProjectId} />
  </AssistantRuntimeProvider>
}

function FullPageState({ label }: { label: string }) {
  return <div className={ui.fullPageState}><OwlMascot size={28} /><span>{label}</span></div>
}

function Workspace({ projectId }: { projectId: string }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [panelOpen, setPanelOpen] = useState(false)
  const [page, setPage] = useState<Page>('chat')
  return <div className={ui.app} data-sidebar-closed={!sidebarOpen} data-graph-open={panelOpen && page === 'chat'}>
    <Sidebar page={page} onNavigate={setPage} onClose={() => setSidebarOpen(false)} />
    <main className={ui.main}>
      <AppHeader page={page} sidebarOpen={sidebarOpen} panelOpen={panelOpen} onOpenSidebar={() => setSidebarOpen(true)} onTogglePanel={() => setPanelOpen(!panelOpen)} />
      {page === 'chat' ? <ChatThread projectId={projectId} /> : <DocumentsPage projectId={projectId} />}
    </main>
    {page === 'chat' && <IntelligencePanel projectId={projectId} open={panelOpen} onClose={() => setPanelOpen(false)} />}
    {sidebarOpen && <button className={ui.mobileOverlay} aria-label="Close sidebar" onClick={() => setSidebarOpen(false)} />}
  </div>
}

function Sidebar({ page, onNavigate, onClose }: { page: Page; onNavigate: (page: Page) => void; onClose: () => void }) {
  const { projects, activeProjectId } = useProjects()
  const [searchOpen, setSearchOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [membersOpen, setMembersOpen] = useState(false)
  const aui = useAui()
  const { user } = useAuth()
  const normalizedSearch = search.trim().toLowerCase()
  async function startNewChat() { onNavigate('chat'); await aui.threads.switchToNewThread() }

  return <aside className={ui.sidebar}>
    <div className={ui.sidebarTop}><button className={`${ui.iconButton} ${ui.mobileMenu}`} onClick={onClose}><Menu size={18} /></button><div className={ui.brand}><span><AppIcon size={27} /></span>intellect</div><div className={ui.sidebarTopActions}><button className={ui.iconButton} aria-label="Manage project members" onClick={() => setMembersOpen(true)}><Users size={17} /></button><button className={ui.iconButton} aria-label="Create project" onClick={() => setCreateOpen(true)}><Plus size={17} /></button></div></div>
    <label className={ui.projectSelectLabel}>Project</label>
    <select className={ui.projectSelect} value={activeProjectId || ''} onChange={(event) => projectStore.select(event.target.value)}>{projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}</select>
    <nav className={ui.primaryNav}><button data-active={page === 'chat'} onClick={() => onNavigate('chat')}><MessageSquare size={16} />Chat</button><button data-active={page === 'documents'} onClick={() => onNavigate('documents')}><Files size={16} />Documents</button></nav>
    {page === 'chat' && <ThreadListPrimitive.Root><button className={ui.newChat} type="button" onClick={() => void startNewChat()}><Plus size={16} />New chat</button><div className={ui.history}><div className={ui.historyHeading}><p>Conversations</p><button onClick={() => setSearchOpen(!searchOpen)}>Search</button></div>{searchOpen && <div className={ui.sidebarSearch}><input autoFocus value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search conversations" /><button onClick={() => { setSearch(''); setSearchOpen(false) }}><X size={14} /></button></div>}<ThreadListPrimitive.Items>{({ threadListItem }) => !normalizedSearch || threadListItem.title?.toLowerCase().includes(normalizedSearch) ? <ThreadListItem projectId={activeProjectId || 'current'} /> : null}</ThreadListPrimitive.Items></div></ThreadListPrimitive.Root>}
    <div className={ui.sidebarBottom}><span className={ui.avatar}>{initials(user?.display_name || 'User')}</span><div><b>{user?.display_name || 'Team member'}</b><small>{user?.email || 'Project workspace'}</small></div><button className={ui.logoutButton} aria-label="Sign out" title="Sign out" onClick={() => void authStore.logout()}><LogOut size={16} /></button></div>
    <CreateProjectDialog open={createOpen} onOpenChange={setCreateOpen} />
    {activeProjectId && <ManageMembersDialog projectId={activeProjectId} open={membersOpen} onOpenChange={setMembersOpen} />}
  </aside>
}

function CreateProjectDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const [name, setName] = useState('')
  return <AlertDialog.Root open={open} onOpenChange={onOpenChange}><AlertDialog.Portal><AlertDialog.Overlay className={ui.dialogOverlay} /><AlertDialog.Content className={ui.dialogContent}><AlertDialog.Title className={ui.dialogTitle}>Create project</AlertDialog.Title><AlertDialog.Description className={ui.dialogDescription}>Documents, conversations, graphs, and insights stay isolated inside this project.</AlertDialog.Description><input className={ui.dialogInput} autoFocus value={name} maxLength={120} placeholder="Project name" onChange={(event) => setName(event.target.value)} /><div className={ui.dialogActions}><AlertDialog.Cancel className={ui.dialogCancel}>Cancel</AlertDialog.Cancel><AlertDialog.Action className={ui.dialogDelete} disabled={!name.trim()} onClick={() => { void projectStore.create(name.trim()); setName('') }}>Create</AlertDialog.Action></div></AlertDialog.Content></AlertDialog.Portal></AlertDialog.Root>
}

function ManageMembersDialog({ projectId, open, onOpenChange }: { projectId: string; open: boolean; onOpenChange: (open: boolean) => void }) {
  const [members, setMembers] = useState<ProjectMember[]>([])
  const [memberId, setMemberId] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [role, setRole] = useState<'editor' | 'viewer'>('editor')
  const [myId, setMyId] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    void Promise.all([api.projects.members(projectId), api.session()])
      .then(([projectMembers, identity]) => { setMembers(projectMembers); setMyId(identity.member_id); setError(null) })
      .catch((requestError) => setError(requestError instanceof Error ? requestError.message : 'Unable to load members.'))
  }, [open, projectId])

  async function addMember() {
    if (!memberId.trim()) return
    try {
      const member = await api.projects.addMember(projectId, { member_id: memberId.trim(), display_name: displayName.trim() || undefined, role })
      setMembers((current) => [...current.filter((item) => item.member_id !== member.member_id), member])
      setMemberId(''); setDisplayName(''); setError(null)
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Unable to add member.') }
  }

  return <AlertDialog.Root open={open} onOpenChange={onOpenChange}><AlertDialog.Portal><AlertDialog.Overlay className={ui.dialogOverlay} /><AlertDialog.Content className={`${ui.dialogContent} w-members-dialog!`}><AlertDialog.Title className={ui.dialogTitle}>Project members</AlertDialog.Title><AlertDialog.Description className={ui.dialogDescription}>Share your collaboration ID with an owner, or add a teammate using the ID from their session.</AlertDialog.Description><div className={ui.memberIdentity}><span><small>Your collaboration ID</small><code>{myId || 'Loading…'}</code></span><button disabled={!myId} onClick={() => void navigator.clipboard.writeText(myId)}><Copy size={14} />Copy</button></div><div className={ui.memberList}>{members.map((member) => <div key={member.id}><span><b>{member.display_name || 'Team member'}</b><small>{member.member_id}</small></span><em>{member.role}</em>{member.role !== 'owner' && <button aria-label={`Remove ${member.display_name || member.member_id}`} onClick={() => void api.projects.removeMember(projectId, member.member_id).then(() => setMembers((current) => current.filter((item) => item.id !== member.id)))}><Trash2 size={14} /></button>}</div>)}</div><div className={ui.memberForm}><input value={memberId} placeholder="Teammate collaboration ID" onChange={(event) => setMemberId(event.target.value)} /><input value={displayName} placeholder="Display name (optional)" onChange={(event) => setDisplayName(event.target.value)} /><select value={role} onChange={(event) => setRole(event.target.value as 'editor' | 'viewer')}><option value="editor">Editor</option><option value="viewer">Viewer</option></select><button disabled={!memberId.trim()} onClick={() => void addMember()}><UserPlus size={14} />Add member</button></div>{error && <p className={ui.memberError}>{error}</p>}<div className={ui.dialogActions}><AlertDialog.Cancel className={ui.dialogCancel}>Done</AlertDialog.Cancel></div></AlertDialog.Content></AlertDialog.Portal></AlertDialog.Root>
}

function ThreadListItem({ projectId }: { projectId: string }) {
  const aui = useAui()
  const threadId = useAuiState((state) => state.threadListItem.remoteId || state.threadListItem.id)
  const title = useAuiState((state) => state.threadListItem.title) || 'this conversation'
  const [confirmOpen, setConfirmOpen] = useState(false)
  return <ThreadListItemPrimitive.Root className={ui.threadListItem}><ThreadListItemPrimitive.Trigger><ThreadListItemPrimitive.Title fallback="New conversation" /></ThreadListItemPrimitive.Trigger><button className={ui.deleteThread} type="button" aria-label={`Delete ${title}`} onClick={(event) => { event.preventDefault(); event.stopPropagation(); setConfirmOpen(true) }}><Trash2 size={14} /></button><ConfirmDeleteDialog open={confirmOpen} title="Delete conversation?" description={`“${title}” will be permanently removed for every project member.`} onOpenChange={setConfirmOpen} onConfirm={() => { chatGraphStore.clear(`${projectId}:${threadId}`); void aui.threads.item({ id: threadId }).delete(); setConfirmOpen(false) }} /></ThreadListItemPrimitive.Root>
}

function ConfirmDeleteDialog({ open, title, description, onOpenChange, onConfirm }: { open: boolean; title: string; description: string; onOpenChange: (open: boolean) => void; onConfirm: () => void }) {
  return <AlertDialog.Root open={open} onOpenChange={onOpenChange}><AlertDialog.Portal><AlertDialog.Overlay className={ui.dialogOverlay} /><AlertDialog.Content className={ui.dialogContent}><AlertDialog.Title className={ui.dialogTitle}>{title}</AlertDialog.Title><AlertDialog.Description className={ui.dialogDescription}>{description}</AlertDialog.Description><div className={ui.dialogActions}><AlertDialog.Cancel className={ui.dialogCancel}>Cancel</AlertDialog.Cancel><AlertDialog.Action className={ui.dialogDelete} onClick={onConfirm}>Delete</AlertDialog.Action></div></AlertDialog.Content></AlertDialog.Portal></AlertDialog.Root>
}

function AppHeader({ page, sidebarOpen, panelOpen, onOpenSidebar, onTogglePanel }: { page: Page; sidebarOpen: boolean; panelOpen: boolean; onOpenSidebar: () => void; onTogglePanel: () => void }) {
  const title = useAuiState((state) => state.threadListItem.title)
  return <header className={ui.header}><div className={ui.headerLeft}>{!sidebarOpen && <button className={ui.iconButton} onClick={onOpenSidebar}><Menu size={18} /></button>}<div className={ui.workspace}>{page === 'documents' ? 'Documents' : title || 'New conversation'}</div></div>{page === 'chat' && <button className={ui.graphToggle} data-active={panelOpen} onClick={onTogglePanel}><GitBranch size={16} /><span>Project intelligence</span></button>}</header>
}

function ChatThread({ projectId }: { projectId: string }) {
  return <ThreadPrimitive.Root className={ui.thread}><ThreadPrimitive.Viewport className={ui.viewport}><AuiIf condition={(state) => state.thread.isEmpty}><Welcome /></AuiIf><ThreadPrimitive.Messages>{({ message }) => message.role === 'user' ? <UserMessage /> : <AssistantMessage />}</ThreadPrimitive.Messages><AuiIf condition={(state) => state.thread.isRunning}><ProcessingStatus /></AuiIf><ThreadPrimitive.ViewportFooter className={ui.footer}><Composer projectId={projectId} /><small>Answers are retrieved only from documents in the current project.</small></ThreadPrimitive.ViewportFooter></ThreadPrimitive.Viewport></ThreadPrimitive.Root>
}

function Welcome() {
  const suggestions = ['Summarize the key ideas', 'Connect related concepts', 'Create a prioritized study plan']
  return <div className={ui.welcome}><span><OwlMascot size={29} /></span><h1>What do you want to understand?</h1><p>Add sources in Documents, then ask a grounded question inside this project.</p><div>{suggestions.map((prompt) => <ThreadPrimitive.Suggestion key={prompt} prompt={prompt}>{prompt}</ThreadPrimitive.Suggestion>)}</div></div>
}

function UserMessage() {
  const messageId = useAuiState((state) => state.message.id)
  const author = usePromptAuthor(messageId)
  return <MessagePrimitive.Root className={`${ui.message} ${ui.userMessage}`}><div className={ui.userMessageStack}><span className={ui.messageAuthor}>{author?.display_name || 'Team member'}</span><div className={ui.userMessageContent}><MessagePrimitive.Parts /></div></div></MessagePrimitive.Root>
}
function AssistantMessage() { return <MessagePrimitive.Root className={`${ui.message} ${ui.assistantMessage}`}><span className={ui.assistantMark}><AppIcon size={32} /></span><div className={ui.assistantMessageContent}><MessagePrimitive.Parts components={{ Text: MarkdownAnswer, data: { by_name: { 'rag-evidence': AnswerEvidence } } }} /></div></MessagePrimitive.Root> }

function Composer({ projectId }: { projectId: string }) {
  return <ComposerPrimitive.Root className={ui.composer}><DraftRestore projectId={projectId} /><ComposerPrimitive.Input className={ui.input} placeholder="Ask about this project's documents…" rows={1} /><div className={ui.composerActions}><span className={ui.composerScope}><Files size={14} />Project sources</span><AuiIf condition={(state) => !state.thread.isRunning}><ComposerPrimitive.Send className={ui.send}><ArrowUp size={17} /></ComposerPrimitive.Send></AuiIf><AuiIf condition={(state) => state.thread.isRunning}><ComposerPrimitive.Cancel className={ui.send}><Square size={12} /></ComposerPrimitive.Cancel></AuiIf></div></ComposerPrimitive.Root>
}

function DraftRestore({ projectId }: { projectId: string }) {
  const aui = useAui(); const text = useAuiState((state) => state.composer.text); const ready = useRef(false); const key = `intellect-composer-draft:${projectId}`
  useEffect(() => { const draft = window.localStorage.getItem(key); if (draft) aui.composer.setText(draft); ready.current = true }, [aui, key])
  useEffect(() => { if (ready.current) window.localStorage.setItem(key, text) }, [key, text])
  return null
}

function ProcessingStatus() { return <div className={ui.processingStatus}><OwlMascot size={19} /><div><b>Preparing grounded answer</b><span><i />Retrieving project chunks</span><span><i />Checking relevance</span><span><i />Generating response</span></div></div> }

function DocumentsPage({ projectId }: { projectId: string }) {
  const { documents, loading, error } = useDocuments()
  const [pendingUploads, setPendingUploads] = useState<Array<{
    id: string
    filename: string
    fileType: string
    sizeBytes: number
    status: 'uploading' | 'failed'
    error?: string
  }>>([])
  const [documentToDelete, setDocumentToDelete] = useState<{ id: string; filename: string } | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const uploadingCount = pendingUploads.filter((item) => item.status === 'uploading').length

  async function uploadFiles(files: FileList | File[]) {
    const batch = Array.from(files).map((file) => ({
      id: crypto.randomUUID(),
      file,
      filename: file.name,
      fileType: file.name.split('.').pop()?.toUpperCase() || 'FILE',
      sizeBytes: file.size,
      status: 'uploading' as const,
    }))
    if (!batch.length) return
    setPendingUploads((current) => [...batch, ...current])
    if (inputRef.current) inputRef.current.value = ''

    await Promise.all(batch.map(async (item) => {
      try {
        await documentStore.upload(item.file)
        setPendingUploads((current) => current.filter((upload) => upload.id !== item.id))
      } catch (uploadError) {
        setPendingUploads((current) => current.map((upload) => upload.id === item.id
          ? { ...upload, status: 'failed', error: uploadError instanceof Error ? uploadError.message : 'Upload failed.' }
          : upload))
      }
    }))
  }
  async function preview(id: string) { const tab = window.open('', '_blank'); try { const blob = await api.documents.content(projectId, id); const url = URL.createObjectURL(blob); if (tab) tab.location.href = url; window.setTimeout(() => URL.revokeObjectURL(url), 60_000) } catch { tab?.close() } }

  return <section className={ui.documentsPage}><div className={ui.pageHeading}><div><h1>Documents</h1><p>Sources uploaded here are chunked, embedded, and indexed only inside this project.</p></div><button className={ui.primaryButton} onClick={() => inputRef.current?.click()}>{uploadingCount > 0 ? <LoaderCircle className={ui.spin} size={16} /> : <Upload size={16} />}{uploadingCount > 0 ? `${uploadingCount} uploading` : 'Upload documents'}</button><input ref={inputRef} hidden multiple type="file" accept=".pdf,.docx,.md,.txt" onChange={(event) => { if (event.target.files) void uploadFiles(event.target.files) }} /></div><button className={ui.uploadZone} onClick={() => inputRef.current?.click()} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); void uploadFiles(event.dataTransfer.files) }}><Upload size={20} /><b>Drop multiple files here or choose from your computer</b><span>PDF, DOCX, Markdown, or text · up to 50 MB each</span></button>{error && <p className={ui.documentPageError}>{error}</p>}<div className={ui.documentTable}><div className={ui.documentTableHead}><span>Document</span><span>Status</span><span>Size</span><span>Pages</span><span /></div>{loading && documents.length === 0 && pendingUploads.length === 0 && <div className={ui.documentEmpty}><LoaderCircle className={ui.spin} size={18} />Loading documents…</div>}{!loading && documents.length === 0 && pendingUploads.length === 0 && <div className={ui.documentEmpty}><FileText size={21} />No project documents yet.</div>}{pendingUploads.map((upload) => <div className={`${ui.documentTableRow} ${ui.pendingUploadRow}`} key={upload.id}><span className={ui.documentName}><i>{upload.status === 'uploading' ? <LoaderCircle className={ui.spin} size={16} /> : <FileText size={16} />}</i><span><b>{upload.filename}</b><small>{upload.status === 'failed' ? upload.error : upload.fileType}</small></span></span><span><em className={`${ui.documentStatus} ${upload.status === 'uploading' ? ui.uploadingStatus : ''}`} data-status={upload.status}>{upload.status}</em></span><span>{formatBytes(upload.sizeBytes)}</span><span>—</span><span className={ui.rowActions}>{upload.status === 'failed' && <button title="Dismiss" aria-label={`Dismiss ${upload.filename}`} onClick={() => setPendingUploads((current) => current.filter((item) => item.id !== upload.id))}><X size={15} /></button>}</span></div>)}{documents.map((document) => <div className={ui.documentTableRow} key={document.id}><span className={ui.documentName}><i><FileText size={16} /></i><span><b>{document.filename}</b><small>{document.file_type.toUpperCase()}</small></span></span><span><em className={ui.documentStatus} data-status={document.status}>{document.status}</em></span><span>{formatBytes(document.size_bytes)}</span><span>{document.page_count ?? '—'}</span><span className={ui.rowActions}><button disabled={document.status !== 'ready'} title="Preview" onClick={() => void preview(document.id)}><Eye size={15} /></button><button title="Delete" onClick={() => setDocumentToDelete({ id: document.id, filename: document.filename })}><Trash2 size={15} /></button></span></div>)}</div><ConfirmDeleteDialog open={documentToDelete !== null} title="Delete document?" description={documentToDelete ? `${documentToDelete.filename} and all indexed data will be permanently deleted from this project.` : ''} onOpenChange={(open) => { if (!open) setDocumentToDelete(null) }} onConfirm={() => { if (documentToDelete) void documentStore.remove(documentToDelete.id); setDocumentToDelete(null) }} /></section>
}

function formatBytes(bytes: number) { return bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB` }
function initials(name: string) { return name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join('') || 'U' }

type UiMessage = { role: string; content: ReadonlyArray<{ type: string; text?: string }> }
function extractTurns(messages: readonly UiMessage[]): ConversationTurn[] {
  const turns: ConversationTurn[] = []; let question = ''
  for (const message of messages) { const text = message.content.filter((part) => part.type === 'text').map((part) => part.text || '').join(' '); if (message.role === 'user') question = text; if (message.role === 'assistant' && question) { turns.push({ question, answer: text }); question = '' } }
  return turns
}

function IntelligencePanel({ projectId, open, onClose }: { projectId: string; open: boolean; onClose: () => void }) {
  const threadId = useAuiState((state) => state.threadListItem.remoteId || state.threadListItem.id) || 'current'
  const messages = useAuiState((state) => state.thread.messages)
  const graphKey = `${projectId}:${threadId}`
  const graph = useChatGraph(graphKey)
  const [tab, setTab] = useState<'graph' | 'insights'>('graph')
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<{ key: string; message: string } | null>(null)
  const [insights, setInsights] = useState<ConversationInsights | null>(null)
  const turns = extractTurns(messages as unknown as UiMessage[])

  useEffect(() => { void api.insights.get(projectId, threadId).then(setInsights).catch(() => undefined) }, [projectId, threadId])
  async function generate() { if (!turns.length) return; setGenerating(true); setError(null); try { if (tab === 'graph') chatGraphStore.replace(graphKey, await api.knowledgeGraph.fromConversation(projectId, turns)); else setInsights(await api.insights.generate(projectId, threadId, turns)) } catch (requestError) { setError({ key: `${graphKey}:${tab}`, message: requestError instanceof Error ? requestError.message : 'Unable to generate project intelligence.' }) } finally { setGenerating(false) } }
  const currentInsights = insights?.project_id === projectId && insights.thread_id === threadId ? insights : null
  const activeError = error?.key === `${graphKey}:${tab}` ? error.message : null
  const hasResult = tab === 'graph' ? graph.nodes.length > 0 : currentInsights !== null

  return <aside className={ui.graphPanel} aria-hidden={!open}><div className={ui.graphHeader}><div><b>Project intelligence</b><small>Current conversation</small></div><div className={ui.graphHeaderActions}><button className={ui.refreshGraph} disabled={generating || !turns.length} onClick={() => void generate()}>{generating ? <LoaderCircle className={ui.spin} size={14} /> : tab === 'graph' ? <GitBranch size={14} /> : <Lightbulb size={14} />}{hasResult ? 'Regenerate' : 'Generate'}</button><button className={ui.iconButton} onClick={onClose}><PanelRightClose size={18} /></button></div></div><div className={ui.intelligenceTabs}><button data-active={tab === 'graph'} onClick={() => setTab('graph')}><GitBranch size={14} />Graph</button><button data-active={tab === 'insights'} onClick={() => setTab('insights')}><Lightbulb size={14} />Insights</button></div><div className={ui.graphContent}>{tab === 'graph' && graph.nodes.length > 0 && <ChatGraph nodes={graph.nodes} edges={graph.edges} />}{tab === 'insights' && currentInsights && <InsightsView insights={currentInsights} />}{!hasResult && <div className={ui.graphState}><span>{activeError || (generating ? 'Building project intelligence…' : tab === 'graph' ? 'Generate a study graph from this conversation.' : 'Extract key takeaways and prioritized next actions.')}</span><button className={ui.generateGraph} disabled={generating || !turns.length} onClick={() => void generate()}>{generating ? 'Generating…' : `Generate ${tab}`}</button></div>}</div></aside>
}

function InsightsView({ insights }: { insights: ConversationInsights }) {
  return <div className={ui.insightsView}><section><h3>Key takeaways</h3>{insights.takeaways.length ? insights.takeaways.map((item, index) => <article key={`${item.title}-${index}`}><span className={ui.insightNumber}>{index + 1}</span><div><b>{item.title}</b><p>{item.explanation}</p><small>Conversation {item.source_turn_numbers.map((turn) => `#${turn}`).join(', ')}</small></div></article>) : <p className={ui.insightsEmpty}>No reliable takeaways found.</p>}</section><section><h3>What to do</h3>{insights.actions.length ? insights.actions.map((item) => <article key={`${item.rank}-${item.title}`}><span className={ui.priority} data-priority={item.priority}>{item.rank}</span><div><div className={ui.actionMeta}><b>{item.title}</b><em>{item.priority}</em><em>{item.kind.replace('_', ' ')}</em></div><p>{item.rationale}</p><small>Conversation {item.source_turn_numbers.map((turn) => `#${turn}`).join(', ')}</small></div></article>) : <p className={ui.insightsEmpty}>No supported next actions were found.</p>}</section></div>
}
