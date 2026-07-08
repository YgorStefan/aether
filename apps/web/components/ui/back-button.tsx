import Link from 'next/link'

export function BackButton() {
  return (
    <Link
      href="/dashboard"
      className="inline-flex items-center gap-1.5 rounded-lg border border-card-border px-3 py-1.5 text-xs font-medium text-text-secondary transition-colors hover:border-primary/40 hover:bg-card hover:text-text-primary"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
      </svg>
      Voltar
    </Link>
  )
}
