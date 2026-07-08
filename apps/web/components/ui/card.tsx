interface CardProps {
  children: React.ReactNode
  className?: string
}

export function Card({ children, className }: Readonly<CardProps>) {
  return (
    <div
      className={`rounded-card border border-card-border bg-card backdrop-blur-sm ${className ?? ''}`}
    >
      {children}
    </div>
  )
}
