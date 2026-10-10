import type { ReactNode } from 'react'
export function InsightCard({ rank, title, description, turns, priority, badges }: {
  rank: number
  title: string
  description: string
  turns: number[]
  priority?: string
  badges?: ReactNode
}) {
  return (
    <article className="grid grid-cols-[1.6875rem_1fr] gap-2.5 border-t border-neutral-800 py-3.25">
      <span
        data-priority={priority}
        className="grid size-5.75 place-items-center rounded-md bg-neutral-200 text-2xs font-bold text-neutral-900 data-[priority=medium]:bg-neutral-700 data-[priority=medium]:text-neutral-200 data-[priority=low]:bg-neutral-800 data-[priority=low]:text-neutral-400"
      >
        {rank}
      </span>
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-1.5">
          <b className="mr-auto text-xs leading-detail text-neutral-200">
            {title}
          </b>
          {badges}
        </div>
        <p className="mt-1.25 mb-0 text-xs leading-copy text-neutral-400">
          {description}
        </p>
        <small className="mt-1.75 block text-2xs text-neutral-600">Conversation {turns.map(turn => `#${turn}`).join(', ')}</small>
      </div>
    </article>
  )
}
export function InsightBadge({ children }: { children: ReactNode }) {
  return <em className="rounded border border-neutral-700 px-1.25 py-0.75 text-2xs text-neutral-500 capitalize not-italic">
    {children}
  </em>
}
