let activeThreadId: string | null = null

export const chatContext = {
  getThreadId: () => activeThreadId,
  setThreadId: (threadId: string | null) => { activeThreadId = threadId },
}
