import type { ConversationParticipant } from '../api/types'

export function UserAvatar({ name, size = 'small', tooltip = name }: { name: string; size?: 'small' | 'tiny'; tooltip?: string }) {
  const initial = Array.from(name.trim())[0]?.toLocaleUpperCase() || '?'
  return (
    <span title={tooltip} aria-label={name} className={`inline-grid shrink-0 place-items-center rounded-full bg-neutral-200 font-semibold text-neutral-900 ring-2 ring-surface ${size === 'tiny' ? 'size-4 text-[9px]' : 'size-5 text-2xs'}`}>
      {initial}
    </span>
  )
}

export function ContributorAvatars({ participants }: { participants: readonly ConversationParticipant[] }) {
  if (participants.length < 2) return null
  const visible = participants.slice(0, 3)
  const remaining = participants.length - visible.length
  const label = `Shared conversation: ${participants.map(user => user.display_name).join(', ')}`
  const tooltip = participants.map(user => user.display_name).join('\n')
  return (
    <span role="img" aria-label={label} title={tooltip} className="flex shrink-0 items-center -space-x-1.5">
      {visible.map(user => <span key={user.id} aria-hidden="true"><UserAvatar name={user.display_name} tooltip={tooltip} /></span>)}
      {remaining > 0 && <span aria-hidden="true" className="inline-grid size-5 place-items-center rounded-full bg-neutral-700 text-[9px] text-neutral-100 ring-2 ring-surface">+{remaining}</span>}
    </span>
  )
}
