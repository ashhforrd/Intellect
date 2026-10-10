import type { ComponentProps, ReactNode } from 'react'
import * as AlertDialog from '@radix-ui/react-alert-dialog'
type DialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: ReactNode
  description: ReactNode
  wide?: boolean
  children: ReactNode
}
export function Dialog({ open, onOpenChange, title, description, wide = false, children }: DialogProps) {
  return (
    <AlertDialog.Root open={open} onOpenChange={onOpenChange}>
      <AlertDialog.Portal>
        <AlertDialog.Overlay className="fixed inset-0 z-100 animate-dialog-fade bg-black/70" />
        <AlertDialog.Content
          className={`fixed top-1/2 left-1/2 z-101 -translate-x-1/2 -translate-y-1/2 animate-dialog-enter rounded-xl border border-neutral-700 bg-neutral-900 p-5.5 text-neutral-100 shadow-dialog ${wide ? 'w-[min(36.25rem,calc(100vw-2rem))]' : 'w-[min(26.875rem,calc(100vw-2rem))]'}`}
        >
          <AlertDialog.Title className="m-0 text-lg font-semibold text-neutral-50">
            {title}
          </AlertDialog.Title>
          <AlertDialog.Description className="mt-2.5 mb-0 text-sm leading-body text-neutral-400">
            {description}
          </AlertDialog.Description>
          {children}
        </AlertDialog.Content>
      </AlertDialog.Portal>
    </AlertDialog.Root>
  )
}
export function DialogActions({ children }: { children: ReactNode }) {
  return <div className="mt-6 flex justify-end gap-2.25">
    {children}
  </div>
}
export function DialogCancel(props: ComponentProps<typeof AlertDialog.Cancel>) {
  return <AlertDialog.Cancel
    {...props}
    className="h-9.5 rounded-lg border border-neutral-700 bg-neutral-900 px-3.5 py-0 text-xs text-neutral-200 hover:bg-neutral-800"
  />
}
export function DialogAction(props: ComponentProps<typeof AlertDialog.Action>) {
  return <AlertDialog.Action
    {...props}
    className="h-9.5 rounded-lg border border-neutral-100 bg-neutral-100 px-3.5 py-0 text-xs text-neutral-900 hover:bg-white disabled:cursor-not-allowed disabled:opacity-40"
  />
}
