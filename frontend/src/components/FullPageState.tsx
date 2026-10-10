import { OwlMascot } from '../OwlMascot'
export function FullPageState({ label }: { label: string }) {
  return (
    <div className="flex min-h-screen items-center justify-center gap-3 bg-neutral-950 text-sm text-neutral-400">
      <OwlMascot size={28} />
      <span>
        {label}
      </span>
    </div>
  )
}
