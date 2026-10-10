import type { ComponentProps } from 'react'
export function LoginField({ label, ...props }: Omit<ComponentProps<'input'>, 'className'> & { label: string }) {
  return (
    <label className="mt-3.75 grid gap-2 text-xs font-semibold text-neutral-400">
      {label}
      <input
        {...props}
        className="h-11.5 rounded-lg border border-neutral-700 bg-neutral-900 px-3.25 py-0 text-sm text-neutral-100 outline-none focus:border-neutral-500"
      />
    </label>
  )
}
