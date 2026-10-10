import { useEffect, useMemo, type ReactNode } from 'react'
import {
  AssistantRuntimeProvider as RuntimeProvider,
  useLocalRuntime,
  useRemoteThreadListRuntime,
  useAuiState,
  type ChatModelAdapter,
} from '@assistant-ui/react'
import { createLocalStorageAdapter, createSimpleTitleAdapter } from '@assistant-ui/core/react'
import { api, ApiError } from './api/client'
import { documentStore } from './documentStore'
import { projectStore } from './projectStore'
import { chatContext } from './chatContext'
import { authStore } from './authStore'
import { promptAuthorStore } from './promptAuthorStore'

const browserStorage = {
  getItem: async (key: string) => window.localStorage.getItem(key),
  setItem: async (key: string, value: string) => window.localStorage.setItem(key, value),
  removeItem: async (key: string) => window.localStorage.removeItem(key),
}

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
  const threadList = useMemo(() => createLocalStorageAdapter({
    storage: browserStorage,
    prefix: `intellect:${projectId}:`,
    titleGenerator: createSimpleTitleAdapter(),
  }), [projectId])
  const runtime = useRemoteThreadListRuntime({
    adapter: threadList,
    runtimeHook: useApiThreadRuntime,
  })
  return <RuntimeProvider runtime={runtime}><ThreadContextSync />{children}</RuntimeProvider>
}

function useApiThreadRuntime() {
  return useLocalRuntime(apiModel)
}

function ThreadContextSync() {
  const threadId = useAuiState((state) => state.threadListItem.id)
  useEffect(() => {
    chatContext.setThreadId(threadId || null)
    return () => chatContext.setThreadId(null)
  }, [threadId])
  return null
}
