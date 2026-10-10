import { ui } from './ui'
import { useMessagePartText } from '@assistant-ui/react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export function MarkdownAnswer() {
  const { text } = useMessagePartText()
  return <div className={ui.markdown}><ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown></div>
}
