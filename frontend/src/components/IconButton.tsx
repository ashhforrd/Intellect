import type { ComponentProps } from 'react'
export function IconButton({ className = '', type = 'button', ...props }: ComponentProps<'button'>) {
  return <button
    {...props}
    type={type}
    className={`grid size-8.5 place-items-center rounded-lg border-0 bg-transparent p-0 text-neutral-400 hover:bg-neutral-900 hover:text-white ${className}`}
  />
}
