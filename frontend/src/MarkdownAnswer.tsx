import { useMessagePartText } from '@assistant-ui/react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export function MarkdownAnswer() {
  const { text } = useMessagePartText()
  return <div className="markdown-answer"><ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown></div>
}
