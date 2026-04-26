interface BentoGridProps {
  children: React.ReactNode
  className?: string
}

interface BentoItemProps {
  children: React.ReactNode
  className?: string
  colSpan?: 1 | 2 | 3
}

export function BentoGrid({ children, className }: BentoGridProps) {
  return (
    <div className={`grid grid-cols-1 md:grid-cols-3 gap-4 ${className ?? ''}`}>
      {children}
    </div>
  )
}

export function BentoItem({ children, className, colSpan = 1 }: BentoItemProps) {
  const spanClass =
    colSpan === 3 ? 'md:col-span-3' : colSpan === 2 ? 'md:col-span-2' : ''
  return (
    <div className={`${spanClass} ${className ?? ''}`}>
      {children}
    </div>
  )
}
