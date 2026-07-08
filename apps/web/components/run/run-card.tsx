import Link from 'next/link'
import { StatusBadge } from './status-badge'
import type { Run } from '@/lib/api'

function truncate(text: string, max = 80): string {
  return text.length > max ? text.slice(0, max) + '…' : text
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export function RunCard({ run }: Readonly<{ run: Run }>) {
  return (
    <Link
      href={`/run/${run.id}`}
      className="flex items-center justify-between p-3 rounded-lg border border-card-border bg-card hover:border-primary transition-colors min-h-[44px]"
    >
      <div className="flex-1 min-w-0 mr-3">
        <p className="text-sm text-text-primary truncate">{truncate(run.objective)}</p>
        <p className="text-xs text-text-muted mt-0.5">{formatDate(run.created_at)}</p>
      </div>
      <StatusBadge status={run.status} />
    </Link>
  )
}
