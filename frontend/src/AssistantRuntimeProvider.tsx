import { useEffect, useMemo, type ReactNode } from 'react'
import {
  AssistantRuntimeProvider as RuntimeProvider,
  ExportedMessageRepository,
  useLocalRuntime,
  useRemoteThreadListRuntime,
  useAuiState,
  type ChatModelAdapter,
  type RemoteThreadListAdapter,
  type ThreadHistoryAdapter,
  type ThreadMessage,
  type ThreadMessageLike,
} from '@assistant-ui/react'
import { api, ApiError } from './api/client'
import { documentStore } from './documentStore'
import { projectStore } from './projectStore'
import { chatContext } from './chatContext'
import { authStore } from './authStore'
import { promptAuthorStore } from './promptAuthorStore'

async function* streamResponse(text: string, sources: unknown[] = [], abortSignal?: AbortSignal) {
  const units = text.match(/\S+\s*/g) ?? [text]
  const unitsPerFrame = Math.max(2, Math.ceil(units.length / 180))
  let visibleText = ''

  for (let index = 0; index < units.length; index += unitsPerFrame) {
    if (abortSignal?.aborted) throw new DOMException('The request was aborted.', 'AbortError')
    visibleText += units.slice(index, index + unitsPerFrame).join('')
    yield { content: [{ type: 'text' as const, text: visibleText }] }
    await new Promise((resolve) => window.setTimeout(resolve, 12))
  }

  if (sources.length > 0) {
    yield {
      content: [
        { type: 'text' as const, text },
        { type: 'data' as const, name: 'rag-evidence', data: { sources } },
      ],
    }
  }
}

const apiModel: ChatModelAdapter = {
  async *run({ messages, abortSignal }) {
    const question = messages.at(-1)?.content
      .filter((part) => part.type === 'text')
      .map((part) => part.text)
      .join(' ')
    const promptMessageId = messages.at(-1)?.id

    if (!question?.trim()) {
      yield* streamResponse('Please enter a question about your documents.', [], abortSignal)
      return
    }

    const documentState = documentStore.getSnapshot()
    const projectId = projectStore.getSnapshot().activeProjectId
    const threadId = chatContext.getThreadId() || messages[0]?.id || messages.at(-1)?.id
    if (!projectId) {
      yield* streamResponse('Select a project before asking a question.', [], abortSignal)
      return
    }
    if (!threadId) {
      yield* streamResponse('Unable to identify this conversation. Please start a new chat.', [], abortSignal)
      return
    }
    const readyDocuments = documentState.documents.filter((item) => item.status === 'ready')
    if (readyDocuments.length === 0) {
      yield* streamResponse('No project documents are ready yet. Keep the worker running and wait until processing finishes.', [], abortSignal)
      return
    }

    try {
      const currentUser = authStore.getSnapshot().user
      if (promptMessageId && currentUser) promptAuthorStore.set(promptMessageId, currentUser)
      const response = await api.questions.ask({
        project_id: projectId,
        thread_id: threadId,
        question,
        retrieval_limit: 8,
      }, abortSignal)
      if (promptMessageId) promptAuthorStore.set(promptMessageId, response.author)

      yield* streamResponse(response.answer, response.sources, abortSignal)
    } catch (error) {
      if (abortSignal.aborted) throw error
      const message = error instanceof ApiError ? error.message : 'The request could not be completed.'
      yield* streamResponse(`Unable to answer: ${message}`, [], abortSignal)
    }
  },
}

export function AssistantRuntimeProvider({ children, projectId }: { children: ReactNode; projectId: string }) {
  const threadList = useMemo(() => createProjectThreadListAdapter(projectId), [projectId])
  const runtime = useRemoteThreadListRuntime({
    adapter: threadList,
    runtimeHook: useApiThreadRuntime,
  })
  return <RuntimeProvider runtime={runtime}><ThreadContextSync />{children}</RuntimeProvider>
}

function useApiThreadRuntime() {
  return useLocalRuntime(apiModel)
}

function createProjectThreadListAdapter(projectId: string): RemoteThreadListAdapter {
  return {
    async list() {
      const threads = await api.questions.conversations.list(projectId)
      return {
        threads: threads.map((thread) => ({
          status: thread.is_archived ? 'archived' as const : 'regular' as const,
          remoteId: thread.id,
          title: thread.title,
          lastMessageAt: new Date(thread.updated_at),
        })),
      }
    },
    async initialize(threadId) {
      const thread = await api.questions.conversations.create(projectId, threadId)
      return { remoteId: thread.id }
    },
    async fetch(threadId) {
      const thread = await api.questions.conversations.get(projectId, threadId)
      return {
        status: thread.is_archived ? 'archived' as const : 'regular' as const,
        remoteId: thread.id,
        title: thread.title,
        lastMessageAt: new Date(thread.updated_at),
      }
    },
    async rename(threadId, title) {
      await api.questions.conversations.update(projectId, threadId, { title })
    },
    async archive(threadId) {
      await api.questions.conversations.update(projectId, threadId, { is_archived: true })
    },
    async unarchive(threadId) {
      await api.questions.conversations.update(projectId, threadId, { is_archived: false })
    },
    async delete(threadId) {
      await api.questions.conversations.remove(projectId, threadId)
    },
    async generateTitle(threadId, messages) {
      const title = conversationTitle(messages)
      await api.questions.conversations.update(projectId, threadId, { title })
      return titleStream(title)
    },
    unstable_useAdapters: function useProjectThreadAdapters() {
      const threadId = useAuiState(
        (state) => state.threadListItem.remoteId || state.threadListItem.id,
      )
      return useMemo(
        () => threadId ? { history: createConversationHistory(projectId, threadId) } : null,
        [threadId],
      )
    },
  }
}

function createConversationHistory(projectId: string, threadId: string): ThreadHistoryAdapter {
  return {
    async load() {
      const turns = await api.questions.conversation(projectId, threadId)
      const messages: ThreadMessageLike[] = turns.flatMap((turn) => {
        const createdAt = new Date(turn.created_at)
        const userMessageId = `${turn.id}:user`
        promptAuthorStore.set(userMessageId, turn.author)
        return [
          {
            id: userMessageId,
            role: 'user' as const,
            content: [{ type: 'text' as const, text: turn.question }],
            createdAt,
          },
          {
            id: `${turn.id}:assistant`,
            role: 'assistant' as const,
            content: [{ type: 'text' as const, text: turn.answer }],
            createdAt,
            status: { type: 'complete' as const, reason: 'stop' as const },
          },
        ]
      })
      return ExportedMessageRepository.fromArray(messages)
    },
    async append() {},
  }
}

function conversationTitle(messages: readonly ThreadMessage[]) {
  const firstUserMessage = messages.find((message) => message.role === 'user')
  const text = firstUserMessage?.content.find((part) => part.type === 'text')
  const title = text?.type === 'text' ? text.text.trim() : ''
  if (!title) return 'New conversation'
  return title.length > 50 ? `${title.slice(0, 47)}...` : title
}

function titleStream(title: string) {
  return new ReadableStream({
    start(controller) {
      controller.enqueue({ type: 'part-start', path: [0], part: { type: 'text' } })
      controller.enqueue({ type: 'text-delta', path: [0], textDelta: title })
      controller.enqueue({ type: 'part-finish', path: [0] })
      controller.close()
    },
  }) as never
}

function ThreadContextSync() {
  const threadId = useAuiState(
    (state) => state.threadListItem.remoteId || state.threadListItem.id,
  )
  useEffect(() => {
    chatContext.setThreadId(threadId || null)
    return () => chatContext.setThreadId(null)
  }, [threadId])
  return null
}
