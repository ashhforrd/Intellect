type OwlMascotProps = {
  className?: string
  size?: number
}

export function OwlMascot({ className, size = 24 }: OwlMascotProps) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path d="M11 17 8 8l10 5M37 17l3-9-10 5" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M24 10c10 0 16 7 16 17 0 9-7 15-16 15S8 36 8 27c0-10 6-17 16-17Z" fill="currentColor"/>
      <circle cx="17" cy="25" r="7" fill="white"/>
      <circle cx="31" cy="25" r="7" fill="white"/>
      <circle cx="18" cy="25" r="2.5" fill="#111"/>
      <circle cx="30" cy="25" r="2.5" fill="#111"/>
      <path d="m24 28-4 4h8l-4-4Z" fill="#777"/>
      <path d="M17 36c4 3 10 3 14 0" stroke="white" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  )
}
