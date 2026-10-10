import type { ReactNode } from 'react'
type DocumentRowProps = {
  filename: string
  detail: ReactNode
  icon: ReactNode
  status: string
  size: string
  pages: ReactNode
  pending?: boolean
  children: ReactNode
}
export function DocumentRow({ filename, detail, icon, status, size, pages, pending = false, children }: DocumentRowProps) {
  return (
    <div
      className={`document-grid min-h-16 border-t border-neutral-800 text-xs text-neutral-400 hover:bg-neutral-900 compact:grid-cols-[1fr_auto] compact:gap-2 compact:py-3.25 ${pending ? 'bg-neutral-900' : ''}`}
    >
      <span className="flex min-w-0 items-center gap-2.5">
        <i className="grid size-8 shrink-0 place-items-center rounded-lg bg-neutral-900 text-neutral-300">
          {icon}
        </i>
        <span className="block min-w-0">
          <b className="block min-w-0 truncate text-xs font-medium text-neutral-100">
            {filename}
          </b>
          <small className={`mt-1 block min-w-0 text-2xs text-neutral-600 ${pending ? 'max-w-135 truncate' : ''}`}>
            {detail}
          </small>
        </span>
      </span>
      <span className="compact:hidden">
        <em
          data-status={status}
          className="inline-flex rounded-md bg-neutral-800 px-1.75 py-1 text-2xs text-neutral-400 capitalize not-italic data-[status=ready]:text-neutral-100 data-[status=failed]:text-danger data-[status=uploading]:text-neutral-200 data-[status=uploading]:before:mr-1.5 data-[status=uploading]:before:size-1.25 data-[status=uploading]:before:animate-upload-pulse data-[status=uploading]:before:rounded-full data-[status=uploading]:before:bg-current data-[status=uploading]:before:content-['']"
        >
          {status}
        </em>
      </span>
      <span className="compact:hidden">
        {size}
      </span>
      <span className="compact:hidden">
        {pages}
      </span>
      <span className="document-actions flex justify-end gap-1.25">
        {children}
      </span>
    </div>
  )
}
