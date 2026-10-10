import type {
  AttachmentAdapter,
  CompleteAttachment,
  PendingAttachment,
} from '@assistant-ui/react'
import { documentStore } from './documentStore'

const acceptedTypes = '.pdf,.docx,.md,.txt'
const maxDocumentSizeBytes = 50 * 1024 * 1024

export class DocumentAttachmentAdapter implements AttachmentAdapter {
  accept = acceptedTypes

  async *add({ file }: { file: File }): AsyncGenerator<PendingAttachment> {
    if (file.size > maxDocumentSizeBytes) throw new Error('File exceeds the 50 MB limit')

    const attachment = {
      id: crypto.randomUUID(),
      type: 'document' as const,
      name: file.name,
      file,
      contentType: file.type,
    }

    yield { ...attachment, status: { type: 'running', reason: 'uploading', progress: 0.05 } }
    const document = await documentStore.upload(file)
    yield { ...attachment, status: { type: 'running', reason: 'uploading', progress: 0.55 } }
    await documentStore.waitUntilReady(document.id)
    yield { ...attachment, status: { type: 'running', reason: 'uploading', progress: 1 } }
    yield { ...attachment, status: { type: 'requires-action', reason: 'composer-send' } }
  }

  async send(attachment: PendingAttachment): Promise<CompleteAttachment> {
    return {
      id: attachment.id,
      type: 'document',
      name: attachment.name,
      contentType: attachment.contentType,
      content: [{ type: 'text', text: `Use the attached document: ${attachment.name}` }],
      status: { type: 'complete' },
    }
  }

  async remove(): Promise<void> {}
}
