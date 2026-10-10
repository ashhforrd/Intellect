import type { ComponentProps } from 'react'
export function NavigationButton({ active, ...props }: Omit<ComponentProps<'button'>, 'className'> & { active: boolean }) {
  return <button
    {...props}
    type="button"
    data-active={active}
    aria-pressed={active}
    className="flex h-full items-center justify-center gap-1.75 rounded-lg border-0 bg-transparent text-xs text-neutral-500 hover:bg-neutral-900 hover:text-neutral-100 data-[active=true]:bg-neutral-900 data-[active=true]:text-neutral-100"
  />
}
