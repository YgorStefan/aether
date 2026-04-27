'use client'

const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  created:   { label: 'Criado',     className: 'bg-[#1f1f1f] text-[var(--color-text-muted)]' },
  running:   { label: 'Executando', className: 'bg-blue-950 text-[var(--color-primary-blue)] animate-pulse' },
  paused:    { label: 'Pausado',    className: 'bg-yellow-950 text-[var(--color-warning)] animate-pulse' },
  completed: { label: 'Concluído',  className: 'bg-green-950 text-[var(--color-success)]' },
  failed:    { label: 'Falhou',     className: 'bg-red-950 text-[var(--color-error)]' },
  cancelled: { label: 'Cancelado',  className: 'bg-[#1f1f1f] text-[var(--color-text-muted)]' },
}

interface StatusBadgeProps {
  status: string
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status.toLowerCase()] ?? STATUS_CONFIG.created
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${config.className}`}>
      {config.label}
    </span>
  )
}
