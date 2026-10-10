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

const apiModel: ChatModelAdapter = {
  async run({ messages, abortSignal }) {
    const question = messages.at(-1)?.content
      .filter((part) => part.type === 'text')
      .map((part) => part.text)
      .join(' ')
    const promptMessageId = messages.at(-1)?.id

    if (!question?.trim()) {
      return { content: [{ type: 'text', text: 'Please enter a question about your documents.' }] }
    }

    const documentState = documentStore.getSnapshot()
    const projectId = projectStore.getSnapshot().activeProjectId
    const threadId = chatContext.getThreadId() || messages[0]?.id || messages.at(-1)?.id
    if (!projectId) {
      return { content: [{ type: 'text', text: 'Select a project before asking a question.' }] }
    }
    if (!threadId) {
      return { content: [{ type: 'text', text: 'Unable to identify this conversation. Please start a new chat.' }] }
    }
    const activeDocument = documentState.documents.find((item) => item.id === documentState.activeDocumentId)
    if (activeDocument && activeDocument.status !== 'ready') {
      return { content: [{ type: 'text', text: `**${activeDocument.filename}** is still ${activeDocument.status}. Keep the worker running and wait until it is ready.` }] }
    }

    try {
      const currentUser = authStore.getSnapshot().user
      if (promptMessageId && currentUser) promptAuthorStore.set(promptMessageId, currentUser)
      const response = await api.questions.ask({
        project_id: projectId,
        thread_id: threadId,
        question,
        document_id: documentState.activeDocumentId || undefined,
        retrieval_limit: 5,
      }, abortSignal)
      if (promptMessageId) promptAuthorStore.set(promptMessageId, response.author)

      return {
        content: [
          { type: 'text', text: response.answer },
          { type: 'data', name: 'rag-evidence', data: { sources: response.sources } },
        ],
      }
    } catch (error) {
      if (abortSignal.aborted) throw error
      const message = error instanceof ApiError ? error.message : 'The request could not be completed.'
      return { content: [{ type: 'text', text: `Unable to answer: ${message}` }] }
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
