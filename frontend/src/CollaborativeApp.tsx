import { InsightCard, InsightBadge } from './components/InsightCard'
import { DocumentRow } from './components/DocumentRow'
import { useEffect, useRef, useState } from 'react'
import { Dialog, DialogActions, DialogCancel, DialogAction } from './components/Dialog'
import { FullPageState } from './components/FullPageState'
import { IconButton } from './components/IconButton'
import { NavigationButton } from './components/NavigationButton'
import { AuiIf, ComposerPrimitive, MessagePrimitive, ThreadListItemPrimitive, ThreadListPrimitive, ThreadPrimitive, useAui, useAuiState, } from '@assistant-ui/react'
import { ArrowUp, Copy, Eye, FileText, Files, GitBranch, Lightbulb, LoaderCircle, LogOut, Menu, MessageSquare, PanelRightClose, Plus, Square, Trash2, Upload, UserPlus, Users, X, } from 'lucide-react'
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
    if (!activeProjectId)
      return
    void documentStore.setProject(activeProjectId)
    const polling = window.setInterval(() => void documentStore.refreshProcessing(), 3000)
    return () => window.clearInterval(polling)
  }, [activeProjectId])
  if (loading && !activeProjectId)
    return <FullPageState label="Opening your projects…" />
  if (error && !activeProjectId)
    return <FullPageState label={error} />
  if (!activeProjectId)
    return <FullPageState label="No project is available." />
  return <AssistantRuntimeProvider key={activeProjectId} projectId={activeProjectId}>
    <Workspace projectId={activeProjectId} />
  </AssistantRuntimeProvider>
}
function Workspace({ projectId }: {
  projectId: string
}) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [panelOpen, setPanelOpen] = useState(false)
  const [page, setPage] = useState<Page>('chat')
  return <div
    data-sidebar-closed={!sidebarOpen}
    data-graph-open={panelOpen && page === 'chat'}
    className="group/app grid min-h-screen [grid-template-columns:17.5rem_minmax(0,_1fr)_0] bg-neutral-950 text-neutral-100 transition-[grid-template-columns] duration-350 ease-panel data-[sidebar-closed=true]:[grid-template-columns:0_minmax(0,_1fr)_0] data-[graph-open=true]:[grid-template-columns:17.5rem_minmax(0,_1fr)_minmax(0,_1fr)] data-[sidebar-closed=true]:data-[graph-open=true]:[grid-template-columns:0_minmax(0,_1fr)_minmax(0,_1fr)] tablet:[grid-template-columns:15rem_minmax(0,_1fr)_0] tablet:data-[sidebar-closed=true]:[grid-template-columns:0_minmax(0,_1fr)_0] tablet:data-[graph-open=true]:[grid-template-columns:15rem_minmax(0,_1fr)_0] tablet:data-[sidebar-closed=true]:data-[graph-open=true]:[grid-template-columns:0_minmax(0,_1fr)_0] mobile:block"
  >
    <Sidebar page={page} onNavigate={setPage} onClose={() => setSidebarOpen(false)} />
    <main className="flex h-screen min-w-0 flex-col bg-neutral-950">
      <AppHeader
        page={page}
        sidebarOpen={sidebarOpen}
        panelOpen={panelOpen}
        onOpenSidebar={() => setSidebarOpen(true)}
        onTogglePanel={() => setPanelOpen(!panelOpen)}
      />
      {page === 'chat' ? <ChatThread projectId={projectId} /> : <DocumentsPage projectId={projectId} />}
    </main>
    {page === 'chat' && <IntelligencePanel projectId={projectId} open={panelOpen} onClose={() => setPanelOpen(false)} />}
    {sidebarOpen && <button
      aria-label="Close sidebar"
      onClick={() => setSidebarOpen(false)}
      className="hidden mobile:fixed mobile:inset-0 mobile:z-9 mobile:block mobile:border-0 mobile:bg-black/75"
    />}
  </div>
}
function Sidebar({ page, onNavigate, onClose }: {
  page: Page
  onNavigate: (page: Page) => void
  onClose: () => void
}) {
  const { projects, activeProjectId } = useProjects()
  const [searchOpen, setSearchOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [membersOpen, setMembersOpen] = useState(false)
  const aui = useAui()
  const { user } = useAuth()
  const normalizedSearch = search.trim().toLowerCase()
  async function startNewChat() { onNavigate('chat'); await aui.threads.switchToNewThread() }
  return <aside
    className="flex h-screen flex-col overflow-hidden whitespace-nowrap border-r border-neutral-800 bg-surface px-3.75 pt-4.5 pb-3.5 [transition:opacity_.25s_ease,_translate_.35s_var(--ease-panel)] group-data-[sidebar-closed=true]/app:invisible group-data-[sidebar-closed=true]/app:opacity-0 group-data-[sidebar-closed=true]/app:-translate-x-6 mobile:fixed mobile:top-0 mobile:left-0 mobile:z-10 mobile:w-65 mobile:group-data-[sidebar-closed=true]/app:-translate-x-full"
  >
    <div className="flex h-9.5 items-center justify-between">
      <IconButton onClick={onClose} className="hidden tablet:grid">
        <Menu size={18} />
      </IconButton>
      <div className="flex items-center gap-2 pl-1.25 text-lg font-bold tracking-brand text-neutral-50"><span className="grid size-6.75 place-items-center rounded-lg bg-neutral-50 text-neutral-950">
        <AppIcon size={27} />
      </span>intellect</div>
      <div className="flex items-center gap-0.5">
        <IconButton aria-label="Manage project members" onClick={() => setMembersOpen(true)}>
          <Users size={17} />
        </IconButton>
        <IconButton aria-label="Create project" onClick={() => setCreateOpen(true)}>
          <Plus size={17} />
        </IconButton>
      </div>
    </div>
    <label className="mx-2 mt-5.5 mb-1.75 block text-2xs font-bold tracking-eyebrow text-neutral-500">Project</label>
    <select
      value={activeProjectId || ''}
      onChange={(event) => projectStore.select(event.target.value)}
      className="font-mono h-10.5 w-full rounded-lg border border-neutral-700 bg-neutral-900 pr-8.5 pl-2.75 text-xs text-neutral-100 outline-none focus:border-neutral-500"
    >
      {projects.map((project) => <option key={project.id} value={project.id}>
        {project.name}
      </option>)}
    </select>
    <nav className="mt-3.25 grid h-9.5 grid-cols-2 gap-1.5">
      <NavigationButton active={page === 'chat'} onClick={() => onNavigate('chat')}><MessageSquare size={16} />Chat</NavigationButton>
      <NavigationButton active={page === 'documents'} onClick={() => onNavigate('documents')}><Files size={16} />Documents</NavigationButton>
    </nav>
    {page === 'chat' && <ThreadListPrimitive.Root>
      <button
        type="button"
        onClick={() => void startNewChat()}
        className="mt-5.5 flex h-11.5 w-full items-center gap-2.25 rounded-lg border border-neutral-700 bg-neutral-900 px-3.75 py-0 text-sm font-semibold text-neutral-100 hover:border-accent hover:bg-neutral-900"
      ><Plus size={16} />New chat</button>
      <div className="mt-7">
        <div className="mx-2.5 mb-2 flex items-center justify-between">
          <p className="m-0 text-xs font-bold tracking-label text-neutral-400">Conversations</p>
          <button onClick={() => setSearchOpen(!searchOpen)} className="border-0 bg-transparent p-0 text-2xs text-neutral-500 hover:text-neutral-200">Search</button>
        </div>
        {searchOpen && <div className="mt-4 flex h-10.5 items-center gap-2 rounded-lg border border-neutral-700 bg-neutral-900 px-2.5">
          <input
            autoFocus
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search conversations"
            className="min-w-0 flex-1 border-0 bg-transparent text-xs text-neutral-100 outline-none placeholder:font-mono placeholder:[font-size:inherit] placeholder:font-normal placeholder:tracking-normal"
          />
          <button
            onClick={() => { setSearch(''); setSearchOpen(false) }}
            className="grid place-items-center border-0 bg-transparent p-0.5 text-neutral-500"
          >
            <X size={14} className="shrink-0 text-neutral-400" />
          </button>
        </div>}
        <ThreadListPrimitive.Items>
          {({ threadListItem }) => !normalizedSearch || threadListItem.title?.toLowerCase().includes(normalizedSearch) ? <ThreadListItem projectId={activeProjectId || 'current'} /> : null}
        </ThreadListPrimitive.Items>
      </div>
    </ThreadListPrimitive.Root>}
    <div
      className="mt-auto grid [grid-template-columns:2.375rem_1fr_auto] items-center gap-2 border-t border-neutral-800 px-1.75 pt-3.25 pb-0.75"
    >
      <span className="grid size-9 place-items-center rounded-full bg-neutral-100 text-xs font-bold text-neutral-900">
        {initials(user?.display_name || 'User')}
      </span>
      <div>
        <b className="block text-xs text-neutral-100">
          {user?.display_name || 'Team member'}
        </b>
        <small className="mt-0.75 block text-2xs text-neutral-500">
          {user?.email || 'Project workspace'}
        </small>
      </div>
      <button
        aria-label="Sign out"
        title="Sign out"
        onClick={() => void authStore.logout()}
        className="grid size-8 place-items-center rounded-lg border-0 bg-transparent p-0 text-neutral-500 hover:bg-neutral-800 hover:text-white"
      >
        <LogOut size={16} className="text-evidence-muted" />
      </button>
    </div>
    <CreateProjectDialog open={createOpen} onOpenChange={setCreateOpen} />
    {activeProjectId && <ManageMembersDialog projectId={activeProjectId} open={membersOpen} onOpenChange={setMembersOpen} />}
  </aside>
}
function CreateProjectDialog({ open, onOpenChange }: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const [name, setName] = useState('')
  return <Dialog
    open={open}
    onOpenChange={onOpenChange}
    title="Create project"
    description="Documents, conversations, graphs, and insights stay isolated inside this project."
  >
    <input
      autoFocus
      value={name}
      maxLength={120}
      placeholder="Project name"
      onChange={(event) => setName(event.target.value)}
      className="mt-4.5 h-10.5 w-full rounded-lg border border-neutral-700 bg-neutral-950 px-3 py-0 text-sm text-neutral-100 outline-none focus:border-neutral-500"
    />
    <DialogActions>
      <DialogCancel >Cancel</DialogCancel>
      <DialogAction disabled={!name.trim()} onClick={() => { void projectStore.create(name.trim()); setName('') }}>Create</DialogAction>
    </DialogActions>
  </Dialog>
}
function ManageMembersDialog({ projectId, open, onOpenChange }: {
  projectId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const [members, setMembers] = useState<ProjectMember[]>([])
  const [memberId, setMemberId] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [role, setRole] = useState<'editor' | 'viewer'>('editor')
  const [myId, setMyId] = useState('')
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    if (!open)
      return
    void Promise.all([api.projects.members(projectId), api.session()])
      .then(([projectMembers, identity]) => { setMembers(projectMembers); setMyId(identity.member_id); setError(null) })
      .catch((requestError) => setError(requestError instanceof Error ? requestError.message : 'Unable to load members.'))
  }, [open, projectId])
  async function addMember() {
    if (!memberId.trim())
      return
    try {
      const member = await api.projects.addMember(projectId, { member_id: memberId.trim(), display_name: displayName.trim() || undefined, role })
      setMembers((current) => [...current.filter((item) => item.member_id !== member.member_id), member])
      setMemberId('')
      setDisplayName('')
      setError(null)
    }
    catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to add member.')
    }
  }
  return <Dialog
    open={open}
    onOpenChange={onOpenChange}
    title="Project members"
    description="Share your collaboration ID with an owner, or add a teammate using the ID from their session."
    wide
  >
    <div className="mt-4.25 flex items-center justify-between gap-3.75 rounded-lg bg-neutral-950 px-3 py-2.75">
      <span className="block min-w-0">
        <small className="block min-w-0 text-2xs text-neutral-500">Your collaboration ID</small>
        <code className="mt-1 block max-w-90 min-w-0 overflow-hidden text-xs text-ellipsis whitespace-nowrap text-neutral-300">
          {myId || 'Loading…'}
        </code>
      </span>
      <button
        disabled={!myId}
        onClick={() => void navigator.clipboard.writeText(myId)}
        className="flex h-8 items-center gap-1.5 rounded-md border-0 bg-neutral-100 px-2.5 py-0 text-2xs text-neutral-900"
      ><Copy size={14} />Copy</button>
    </div>
    <div className="mt-3.5 max-h-45 overflow-y-auto">
      {members.map((member) => <div key={member.id} className="grid min-h-11.5 [grid-template-columns:1fr_auto_1.875rem] items-center gap-2 border-t border-neutral-800">
        <span className="block min-w-0">
          <b className="block min-w-0 text-xs font-medium text-neutral-200">
            {member.display_name || 'Team member'}
          </b>
          <small className="mt-0.75 block min-w-0 overflow-hidden text-2xs text-ellipsis whitespace-nowrap text-neutral-600">
            {member.member_id}
          </small>
        </span>
        <em className="text-2xs text-neutral-500 capitalize not-italic">
          {member.role}
        </em>
        {member.role !== 'owner' && <button
          aria-label={`Remove ${member.display_name || member.member_id}`}
          onClick={() => void api.projects.removeMember(projectId, member.member_id).then(() => setMembers((current) => current.filter((item) => item.id !== member.id)))}
          className="grid size-7 place-items-center rounded-md border-0 bg-transparent text-neutral-500 hover:bg-neutral-800 hover:text-white"
        >
          <Trash2 size={14} />
        </button>}
      </div>)}
    </div>
    <div className="mt-3.75 grid [grid-template-columns:1.5fr_1fr_5.625rem_auto] gap-1.75 compact:grid-cols-1">
      <input
        value={memberId}
        placeholder="Teammate collaboration ID"
        onChange={(event) => setMemberId(event.target.value)}
        className="min-w-0 h-9 rounded-lg border border-neutral-700 bg-neutral-950 px-2.25 py-0 text-2xs text-neutral-200 outline-none"
      />
      <input
        value={displayName}
        placeholder="Display name (optional)"
        onChange={(event) => setDisplayName(event.target.value)}
        className="min-w-0 h-9 rounded-lg border border-neutral-700 bg-neutral-950 px-2.25 py-0 text-2xs text-neutral-200 outline-none"
      />
      <select
        value={role}
        onChange={(event) => setRole(event.target.value as 'editor' | 'viewer')}
        className="min-w-0 h-9 rounded-lg border border-neutral-700 bg-neutral-950 px-2.25 py-0 text-2xs text-neutral-200 outline-none"
      >
        <option value="editor">Editor</option>
        <option value="viewer">Viewer</option>
      </select>
      <button
        disabled={!memberId.trim()}
        onClick={() => void addMember()}
        className="flex h-9 items-center gap-1.5 rounded-md border-0 bg-neutral-100 px-2.5 py-0 text-2xs text-neutral-900 disabled:cursor-not-allowed disabled:opacity-35"
      ><UserPlus size={14} />Add member</button>
    </div>
    {error && <p className="mt-2.25 mb-0 text-2xs text-danger">
      {error}
    </p>}
    <DialogActions>
      <DialogCancel >Done</DialogCancel>
    </DialogActions>
  </Dialog>
}
function ThreadListItem({ projectId }: {
  projectId: string
}) {
  const aui = useAui()
  const threadId = useAuiState((state) => state.threadListItem.remoteId || state.threadListItem.id)
  const title = useAuiState((state) => state.threadListItem.title) || 'this conversation'
  const [confirmOpen, setConfirmOpen] = useState(false)
  return <ThreadListItemPrimitive.Root className="group/thread relative">
    <ThreadListItemPrimitive.Trigger
      className="h-10.5 w-full overflow-hidden rounded-lg border-0 bg-transparent py-0 pr-10.5 pl-3 text-left text-sm text-ellipsis whitespace-nowrap text-neutral-400 hover:bg-neutral-900 hover:text-white group-data-[active=true]/thread:bg-neutral-900 group-data-[active=true]/thread:text-white"
    >
      <ThreadListItemPrimitive.Title fallback="New conversation" />
    </ThreadListItemPrimitive.Trigger>
    <button
      type="button"
      aria-label={`Delete ${title}`}
      onClick={(event) => { event.preventDefault(); event.stopPropagation(); setConfirmOpen(true) }}
      className="absolute top-1.75 right-1.75 grid size-7 place-items-center rounded-md border-0 bg-transparent p-0 text-neutral-500 opacity-0 group-hover/thread:opacity-100 group-focus-within/thread:opacity-100 hover:bg-neutral-800 hover:text-white overflow-hidden text-sm text-left group-data-[active=true]/thread:bg-neutral-900 group-data-[active=true]/thread:text-white"
    >
      <Trash2 size={14} />
    </button>
    <ConfirmDeleteDialog
      open={confirmOpen}
      title="Delete conversation?"
      description={`“${title}” will be permanently removed for every project member.`}
      onOpenChange={setConfirmOpen}
      onConfirm={() => { chatGraphStore.clear(`${projectId}:${threadId}`); void aui.threads.item({ id: threadId }).delete(); setConfirmOpen(false) }}
    />
  </ThreadListItemPrimitive.Root>
}
function ConfirmDeleteDialog({ open, title, description, onOpenChange, onConfirm }: {
  open: boolean
  title: string
  description: string
  onOpenChange: (open: boolean) => void
  onConfirm: () => void
}) {
  return <Dialog open={open} onOpenChange={onOpenChange} title={title} description={description}>
    <DialogActions>
      <DialogCancel >Cancel</DialogCancel>
      <DialogAction onClick={onConfirm}>Delete</DialogAction>
    </DialogActions>
  </Dialog>
}
function AppHeader({ page, sidebarOpen, panelOpen, onOpenSidebar, onTogglePanel }: {
  page: Page
  sidebarOpen: boolean
  panelOpen: boolean
  onOpenSidebar: () => void
  onTogglePanel: () => void
}) {
  const title = useAuiState((state) => state.threadListItem.title)
  return <header className="flex h-17 items-center justify-between border-b border-neutral-800 bg-surface px-6">
    <div className="flex items-center gap-2">
      {!sidebarOpen && <IconButton onClick={onOpenSidebar}>
        <Menu size={18} />
      </IconButton>}
      <div className="flex items-center gap-1.5 border-0 bg-transparent text-xs text-neutral-400">
        {page === 'documents' ? 'Documents' : title || 'New conversation'}
      </div>
    </div>
    {page === 'chat' && <button
      data-active={panelOpen}
      onClick={onTogglePanel}
      className="flex h-9.75 items-center gap-1.75 rounded-lg border border-neutral-700 bg-neutral-900 px-3.5 py-0 text-xs text-neutral-400 hover:border-neutral-100 hover:bg-neutral-900 hover:text-white data-[active=true]:border-neutral-100 data-[active=true]:bg-neutral-900 data-[active=true]:text-white"
    >
      <GitBranch size={16} />
      <span className="mobile:hidden">Project intelligence</span>
    </button>}
  </header>
}
function ChatThread({ projectId }: {
  projectId: string
}) {
  return <ThreadPrimitive.Root className="min-h-0 flex-1 bg-neutral-950">
    <ThreadPrimitive.Viewport className="relative flex h-full flex-col overflow-y-auto bg-neutral-950 px-8.5">
      <AuiIf condition={(state) => state.thread.isEmpty}>
        <Welcome />
      </AuiIf>
      <ThreadPrimitive.Messages>
        {({ message }) => message.role === 'user' ? <UserMessage /> : <AssistantMessage />}
      </ThreadPrimitive.Messages>
      <AuiIf condition={(state) => state.thread.isRunning}>
        <ProcessingStatus />
      </AuiIf>
      <ThreadPrimitive.ViewportFooter
        className="sticky bottom-0 mx-auto mt-auto mb-0 w-full max-w-215 [background-image:linear-gradient(transparent,_var(--color-neutral-950)_25%)] pt-6 pb-7"
      >
        <Composer projectId={projectId} />
        <small className="mt-2.25 block text-center text-2xs text-neutral-600">Answers are retrieved only from documents in the current project.</small>
      </ThreadPrimitive.ViewportFooter>
    </ThreadPrimitive.Viewport>
  </ThreadPrimitive.Root>
}
function Welcome() {
  const suggestions = ['Summarize the key ideas', 'Connect related concepts', 'Create a prioritized study plan']
  return <div className="mx-auto mt-auto mb-0 w-full max-w-210 pt-17.5 text-center">
    <span className="mx-auto mb-5 grid size-11.25 place-items-center rounded-xl bg-neutral-50 text-neutral-950">
      <OwlMascot size={29} />
    </span>
    <h1 className="m-0 text-3xl font-semibold tracking-welcome text-neutral-50 mobile:text-2xl">What do you want to understand?</h1>
    <p className="mt-2.5 mb-0 text-sm text-neutral-400">Add sources in Documents, then ask a grounded question inside this project.</p>
    <div className="mt-7 mb-6 flex justify-center gap-2 mobile:justify-start mobile:overflow-x-auto">
      {suggestions.map((prompt) => <ThreadPrimitive.Suggestion
        key={prompt}
        prompt={prompt}
        className="rounded-full border border-neutral-700 bg-neutral-900 px-3.5 py-2.5 text-xs text-neutral-300 hover:border-neutral-500 hover:bg-neutral-900 hover:text-white mobile:shrink-0"
      >
        {prompt}
      </ThreadPrimitive.Suggestion>)}
    </div>
  </div>
}
function UserMessage() {
  const messageId = useAuiState((state) => state.message.id)
  const author = usePromptAuthor(messageId)
  return <MessagePrimitive.Root className="mx-auto flex w-full max-w-230 gap-3.5 py-3.75 text-base leading-copy mobile:text-sm justify-end">
    <div className="flex max-w-3/4 flex-col items-end gap-1.5">
      <span className="mx-1 mt-0 mb-1.5 block text-right text-2xs text-neutral-500">
        {author?.display_name || 'Team member'}
      </span>
      <div className="max-w-full rounded-user-message bg-neutral-700 px-3.75 py-2.75 text-white message-content">
        <MessagePrimitive.Parts />
      </div>
    </div>
  </MessagePrimitive.Root>
}
function AssistantMessage() {
  return <MessagePrimitive.Root className="mx-auto flex w-full max-w-230 gap-3.5 py-3.75 text-base leading-copy mobile:text-sm justify-start">
    <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-neutral-100 text-neutral-900">
      <AppIcon size={32} />
    </span>
    <div className="max-w-9/10 pt-0.75 text-base whitespace-normal text-neutral-200 message-content">
      <MessagePrimitive.Parts components={{ Text: MarkdownAnswer, data: { by_name: { 'rag-evidence': AnswerEvidence } } }} />
    </div>
  </MessagePrimitive.Root>
}
function Composer({ projectId }: {
  projectId: string
}) {
  return <ComposerPrimitive.Root className="rounded-2xl border border-neutral-700 bg-neutral-900 p-3.75 shadow-none">
    <DraftRestore projectId={projectId} />
    <ComposerPrimitive.Input
      placeholder="Ask about this project's documents…"
      rows={1}
      className="max-h-40 min-h-14.5 w-full resize-none border-0 bg-transparent p-0.5 text-sm leading-body text-neutral-100 outline-none placeholder:font-mono placeholder:[font-size:inherit] placeholder:font-normal placeholder:tracking-normal placeholder:text-neutral-500"
    />
    <div className="mt-1.5 flex items-center justify-end gap-1.75">
      <span className="flex items-center gap-1.5 text-xs text-neutral-500"><Files size={14} />Project sources</span>
      <AuiIf condition={(state) => !state.thread.isRunning}>
        <ComposerPrimitive.Send
          className="ml-auto grid size-9 place-items-center rounded-lg border-0 bg-white text-neutral-900 disabled:cursor-default disabled:bg-neutral-800 disabled:text-neutral-600"
        >
          <ArrowUp size={17} />
        </ComposerPrimitive.Send>
      </AuiIf>
      <AuiIf condition={(state) => state.thread.isRunning}>
        <ComposerPrimitive.Cancel
          className="ml-auto grid size-9 place-items-center rounded-lg border-0 bg-white text-neutral-900 disabled:cursor-default disabled:bg-neutral-800 disabled:text-neutral-600"
        >
          <Square size={12} />
        </ComposerPrimitive.Cancel>
      </AuiIf>
    </div>
  </ComposerPrimitive.Root>
}
function DraftRestore({ projectId }: {
  projectId: string
}) {
  const aui = useAui()
  const text = useAuiState((state) => state.composer.text)
  const ready = useRef(false)
  const key = `intellect-composer-draft:${projectId}`
  useEffect(() => {
    const draft = window.localStorage.getItem(key); if (draft)
      aui.composer.setText(draft); ready.current = true
  }, [aui, key])
  useEffect(() => {
    if (ready.current)
      window.localStorage.setItem(key, text)
  }, [key, text])
  return null
}
function ProcessingStatus() {
  return (
    <div className="mx-auto flex w-full max-w-190 gap-2.5 py-3.25 text-xs text-neutral-200">
      <OwlMascot size={19} className="shrink-0" />
      <div>
        <b className="mb-1.75 block text-neutral-100">Preparing grounded answer</b>
        {['Retrieving project chunks', 'Checking relevance', 'Generating response'].map((step, index) => (
          <span key={step} className="mr-2.5 inline-flex items-center gap-1 text-xs text-neutral-400">
            <i className="size-1.25 animate-process-pulse rounded-full bg-neutral-200" style={{ animationDelay: index * 0.2 + 's' }} />
            {step}
          </span>
        ))}
      </div>
    </div>
  )
}
function DocumentsPage({ projectId }: {
  projectId: string
}) {
  const { documents, loading, error } = useDocuments()
  const [pendingUploads, setPendingUploads] = useState<Array<{
    id: string
    filename: string
    fileType: string
    sizeBytes: number
    status: 'uploading' | 'failed'
    error?: string
  }>>([])
  const [documentToDelete, setDocumentToDelete] = useState<{
    id: string
    filename: string
  } | null>(null)
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
    if (!batch.length)
      return
    setPendingUploads((current) => [...batch, ...current])
    if (inputRef.current)
      inputRef.current.value = ''
    await Promise.all(batch.map(async (item) => {
      try {
        await documentStore.upload(item.file)
        setPendingUploads((current) => current.filter((upload) => upload.id !== item.id))
      }
      catch (uploadError) {
        setPendingUploads((current) => current.map((upload) => upload.id === item.id
          ? { ...upload, status: 'failed', error: uploadError instanceof Error ? uploadError.message : 'Upload failed.' }
          : upload))
      }
    }))
  }
  async function preview(id: string) {
    const tab = window.open('', '_blank'); try {
      const blob = await api.documents.content(projectId, id)
      const url = URL.createObjectURL(blob)
      if (tab)
        tab.location.href = url
      window.setTimeout(() => URL.revokeObjectURL(url), 60000)
    }
    catch {
      tab?.close()
    }
  }
  return <section
    className="mx-auto [width:min(70rem,_calc(100%_-_4rem))] overflow-y-auto pt-12 pb-17.5 compact:[width:calc(100%_-_1.875rem)] compact:pt-7"
  >
    <div className="flex items-start justify-between gap-5 compact:flex-col compact:items-stretch">
      <div>
        <h1 className="m-0 text-3xl leading-tight tracking-title text-neutral-50">Documents</h1>
        <p className="mt-2.25 mb-0 max-w-165 text-sm leading-copy text-neutral-500">Sources uploaded here are chunked, embedded, and indexed only inside this project.</p>
      </div>
      <button
        onClick={() => inputRef.current?.click()}
        className="flex h-10 shrink-0 items-center gap-2 rounded-lg border-0 bg-neutral-100 px-3.5 py-0 text-xs font-semibold text-neutral-900 hover:bg-white disabled:cursor-not-allowed disabled:opacity-50 compact:justify-center"
      >
        {uploadingCount > 0 ? <LoaderCircle size={16} className="animate-document-spin" /> : <Upload size={16} />}
        {uploadingCount > 0 ? `${uploadingCount} uploading` : 'Upload documents'}
      </button>
      <input
        ref={inputRef}
        hidden
        multiple
        type="file"
        accept=".pdf,.docx,.md,.txt"
        onChange={(event) => {
          if (event.target.files)
            void uploadFiles(event.target.files)
        }}
      />
    </div>
    <button
      onClick={() => inputRef.current?.click()}
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => { event.preventDefault(); void uploadFiles(event.dataTransfer.files) }}
      className="mt-8 flex min-h-36 w-full flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-neutral-700 bg-neutral-950 text-neutral-500 hover:border-neutral-500 hover:bg-neutral-900 hover:text-neutral-200"
    >
      <Upload size={20} />
      <b className="text-sm font-medium text-neutral-200">Drop multiple files here or choose from your computer</b>
      <span className="text-xs">PDF, DOCX, Markdown, or text · up to 50 MB each</span>
    </button>
    {error && <p className="mt-3.75 mb-0 text-xs text-danger">
      {error}
    </p>}
    <div className="mt-6 overflow-hidden rounded-xl border border-neutral-800 bg-surface">
      <div className="document-grid h-11 bg-neutral-900 text-2xs font-bold tracking-table text-neutral-500 compact:hidden">
        <span>Document</span>
        <span>Status</span>
        <span>Size</span>
        <span>Pages</span>
        <span />
      </div>
      {loading && documents.length === 0 && pendingUploads.length === 0 && <div className="flex min-h-37.5 items-center justify-center gap-2.25 border-t border-neutral-800 text-xs text-neutral-500"><LoaderCircle size={18} className="animate-document-spin" />Loading documents…</div>}
      {!loading && documents.length === 0 && pendingUploads.length === 0 && <div className="flex min-h-37.5 items-center justify-center gap-2.25 border-t border-neutral-800 text-xs text-neutral-500"><FileText size={21} />No project documents yet.</div>}
      {pendingUploads.map((upload) => <DocumentRow
        key={upload.id}
        pending
        filename={upload.filename}
        detail={upload.status === 'failed' ? upload.error : upload.fileType}
        icon={upload.status === 'uploading' ? <LoaderCircle size={16} className="animate-document-spin" /> : <FileText size={16} />}
        status={upload.status}
        size={formatBytes(upload.sizeBytes)}
        pages={<>—</>}
      >
        {upload.status === 'failed' && <button
          title="Dismiss"
          aria-label={`Dismiss ${upload.filename}`}
          onClick={() => setPendingUploads((current) => current.filter((item) => item.id !== upload.id))}
        >
          <X size={15} />
        </button>}
      </DocumentRow>)}
      {documents.map((document) => <DocumentRow
        key={document.id}
        filename={document.filename}
        detail={document.file_type.toUpperCase()}
        icon={<><FileText size={16} /></>}
        status={document.status}
        size={formatBytes(document.size_bytes)}
        pages={document.page_count ?? '—'}
      >
        <button disabled={document.status !== 'ready'} title="Preview" onClick={() => void preview(document.id)}>
          <Eye size={15} />
        </button>
        <button title="Delete" onClick={() => setDocumentToDelete({ id: document.id, filename: document.filename })}>
          <Trash2 size={15} />
        </button>
      </DocumentRow>)}
    </div>
    <ConfirmDeleteDialog
      open={documentToDelete !== null}
      title="Delete document?"
      description={documentToDelete ? `${documentToDelete.filename} and all indexed data will be permanently deleted from this project.` : ''}
      onOpenChange={(open) => {
        if (!open)
          setDocumentToDelete(null)
      }}
      onConfirm={() => {
        if (documentToDelete)
          void documentStore.remove(documentToDelete.id); setDocumentToDelete(null)
      }}
    />
  </section>
}
function formatBytes(bytes: number) { return bytes < 1024 * 1024 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB` }
function initials(name: string) { return name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join('') || 'U' }
type UiMessage = {
  role: string
  content: ReadonlyArray<{
    type: string
    text?: string
  }>
}
function extractTurns(messages: readonly UiMessage[]): ConversationTurn[] {
  const turns: ConversationTurn[] = []
  let question = ''
  for (const message of messages) {
    const text = message.content.filter((part) => part.type === 'text').map((part) => part.text || '').join(' ')
    if (message.role === 'user')
      question = text
    if (message.role === 'assistant' && question) {
      turns.push({ question, answer: text })
      question = ''
    }
  }
  return turns
}
function IntelligencePanel({ projectId, open, onClose }: {
  projectId: string
  open: boolean
  onClose: () => void
}) {
  const threadId = useAuiState((state) => state.threadListItem.remoteId || state.threadListItem.id) || 'current'
  const messages = useAuiState((state) => state.thread.messages)
  const graphKey = `${projectId}:${threadId}`
  const graph = useChatGraph(graphKey)
  const [tab, setTab] = useState<'graph' | 'insights'>('graph')
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<{
    key: string
    message: string
  } | null>(null)
  const [insights, setInsights] = useState<ConversationInsights | null>(null)
  const turns = extractTurns(messages as unknown as UiMessage[])
  useEffect(() => { void api.insights.get(projectId, threadId).then(setInsights).catch(() => undefined) }, [projectId, threadId])
  async function generate() {
    if (!turns.length)
      return; setGenerating(true); setError(null); try {
        if (tab === 'graph')
          chatGraphStore.replace(graphKey, await api.knowledgeGraph.fromConversation(projectId, turns))
        else
          setInsights(await api.insights.generate(projectId, threadId, turns))
      }
    catch (requestError) {
      setError({ key: `${graphKey}:${tab}`, message: requestError instanceof Error ? requestError.message : 'Unable to generate project intelligence.' })
    }
    finally {
      setGenerating(false)
    }
  }
  const currentInsights = insights?.project_id === projectId && insights.thread_id === threadId ? insights : null
  const activeError = error?.key === `${graphKey}:${tab}` ? error.message : null
  const hasResult = tab === 'graph' ? graph.nodes.length > 0 : currentInsights !== null
  return <aside
    aria-hidden={!open}
    className="invisible h-screen min-w-0 translate-x-6 overflow-hidden border-l border-neutral-800 bg-surface opacity-0 [transition:opacity_.25s_ease,_translate_.35s_var(--ease-panel),_visibility_.35s] group-data-[graph-open=true]/app:visible group-data-[graph-open=true]/app:translate-x-0 group-data-[graph-open=true]/app:opacity-100 tablet:fixed tablet:top-0 tablet:right-0 tablet:z-6 tablet:[width:min(35rem,_92vw)] tablet:shadow-drawer"
  >
    <div className="flex h-17 items-center justify-between border-b border-neutral-800 bg-surface px-5 py-0">
      <div>
        <b className="block text-sm text-neutral-50">Project intelligence</b>
        <small className="mt-1 block text-xs text-neutral-500">Current conversation</small>
      </div>
      <div className="flex items-center gap-1.5">
        <button
          disabled={generating || !turns.length}
          onClick={() => void generate()}
          className="flex h-8.5 items-center gap-1.75 rounded-lg border border-neutral-700 bg-neutral-900 px-2.5 py-0 text-xs text-neutral-300 hover:border-neutral-600 hover:bg-neutral-800 hover:text-white disabled:cursor-not-allowed disabled:opacity-45"
        >
          {generating ? <LoaderCircle size={14} className="animate-document-spin" /> : tab === 'graph' ? <GitBranch size={14} /> : <Lightbulb size={14} />}
          {hasResult ? 'Regenerate' : 'Generate'}
        </button>
        <IconButton onClick={onClose}>
          <PanelRightClose size={18} />
        </IconButton>
      </div>
    </div>
    <div className="grid h-11.75 grid-cols-2 gap-1.25 border-b border-neutral-800 bg-surface px-3.5 py-1.75">
      <NavigationButton active={tab === 'graph'} onClick={() => setTab('graph')}><GitBranch size={14} />Graph</NavigationButton>
      <NavigationButton active={tab === 'insights'} onClick={() => setTab('insights')}><Lightbulb size={14} />Insights</NavigationButton>
    </div>
    <div className="[height:calc(100vh_-_7.1875rem)] min-h-0 overflow-hidden bg-surface graph-surface">
      {tab === 'graph' && graph.nodes.length > 0 && <ChatGraph nodes={graph.nodes} edges={graph.edges} />}
      {tab === 'insights' && currentInsights && <InsightsView insights={currentInsights} />}
      {!hasResult && <div className="flex h-full flex-col items-center justify-center gap-1.75 p-6.25 text-center text-sm text-neutral-500">
        <span>
          {activeError || (generating ? 'Building project intelligence…' : tab === 'graph' ? 'Generate a study graph from this conversation.' : 'Extract key takeaways and prioritized next actions.')}
        </span>
        <button
          disabled={generating || !turns.length}
          onClick={() => void generate()}
          className="h-10 rounded-lg border border-neutral-600 bg-neutral-100 px-4 py-0 text-xs text-neutral-900 hover:bg-white disabled:cursor-not-allowed disabled:opacity-40"
        >
          {generating ? 'Generating…' : `Generate ${tab}`}
        </button>
      </div>}
    </div>
  </aside>
}
function InsightsView({ insights }: { insights: ConversationInsights }) {
  return (
    <div className="h-full overflow-y-auto bg-surface/90 px-5.5 pt-6 pb-15">
      <section>
        <h3 className="mt-0 mb-3.25 text-sm text-neutral-100">Key takeaways</h3>
        {insights.takeaways.length ? insights.takeaways.map((item, index) => (
          <InsightCard
            key={item.title + '-' + index}
            rank={index + 1}
            title={item.title}
            description={item.explanation}
            turns={item.source_turn_numbers}
          />
        )) : <p className="text-xs text-neutral-500">No reliable takeaways found.</p>}
      </section>
      <section className="mt-8.5">
        <h3 className="mt-0 mb-3.25 text-sm text-neutral-100">What to do</h3>
        {insights.actions.length ? insights.actions.map(item => (
          <InsightCard
            key={item.rank + '-' + item.title}
            rank={item.rank}
            title={item.title}
            description={item.rationale}
            turns={item.source_turn_numbers}
            priority={item.priority}
            badges={<><InsightBadge>
              {item.priority}
            </InsightBadge><InsightBadge>
                {item.kind.replace('_', ' ')}
              </InsightBadge></>}
          />
        )) : <p className="text-xs text-neutral-500">No supported next actions were found.</p>}
      </section>
    </div>
  )
}
