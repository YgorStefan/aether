interface CardProps {
  children: React.ReactNode
  className?: string
}

export function Card({ children, className }: CardProps) {
  return (
    <div
      className={`rounded-[var(--radius-card)] border border-[var(--color-card-border)] bg-[var(--color-card)] backdrop-blur-sm ${className ?? ''}`}
    >
      {children}
    </div>
  )
}
