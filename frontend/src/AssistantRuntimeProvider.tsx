import type { ReactNode } from 'react'
import {
  AssistantRuntimeProvider as RuntimeProvider,
  useLocalRuntime,
  useRemoteThreadListRuntime,
  type ChatModelAdapter,
} from '@assistant-ui/react'
import { createLocalStorageAdapter, createSimpleTitleAdapter } from '@assistant-ui/core/react'
import { DocumentAttachmentAdapter } from './DocumentAttachmentAdapter'
import { api, ApiError } from './api/client'
import { documentStore } from './documentStore'

const browserStorage = {
  getItem: async (key: string) => window.localStorage.getItem(key),
  setItem: async (key: string, value: string) => window.localStorage.setItem(key, value),
  removeItem: async (key: string) => window.localStorage.removeItem(key),
}

const threadList = createLocalStorageAdapter({
  storage: browserStorage,
  prefix: 'intellect:',
  titleGenerator: createSimpleTitleAdapter(),
})

const apiModel: ChatModelAdapter = {
  async run({ messages, abortSignal }) {
    const question = messages.at(-1)?.content
      .filter((part) => part.type === 'text')
      .map((part) => part.text)
      .join(' ')

    if (!question?.trim()) {
      return { content: [{ type: 'text', text: 'Please enter a question about your documents.' }] }
    }

    const documentState = documentStore.getSnapshot()
    const activeDocument = documentState.documents.find((item) => item.id === documentState.activeDocumentId)
    if (activeDocument && activeDocument.status !== 'ready') {
      return { content: [{ type: 'text', text: `**${activeDocument.filename}** is still ${activeDocument.status}. Keep the worker running and wait until it is ready.` }] }
    }

    try {
      const response = await api.questions.ask({
        question,
        document_id: documentState.activeDocumentId || undefined,
        retrieval_limit: 5,
      }, abortSignal)

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

export function AssistantRuntimeProvider({ children }: { children: ReactNode }) {
  const runtime = useRemoteThreadListRuntime({
    adapter: threadList,
    runtimeHook: useApiThreadRuntime,
  })
  return <RuntimeProvider runtime={runtime}>{children}</RuntimeProvider>
}

function useApiThreadRuntime() {
  return useLocalRuntime(apiModel, {
    adapters: { attachments: new DocumentAttachmentAdapter() },
  })
}
