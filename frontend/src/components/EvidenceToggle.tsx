import type { ReactNode } from 'react'
import { ChevronDown } from 'lucide-react'
export function EvidenceToggle({ open, onToggle, children }: { open: boolean; onToggle: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      aria-expanded={open}
      onClick={onToggle}
      className="flex w-full items-center gap-1.5 border-0 bg-transparent px-0 py-2.75 text-left text-xs text-neutral-400 hover:text-white"
    >
      {children}
      <ChevronDown size={13} className={`ml-auto transition-transform duration-180 ${open ? 'rotate-180' : ''}`} />
    </button>
  )
}
