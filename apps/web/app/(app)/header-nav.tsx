'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LogoutButton } from '@/components/ui/logout-button'

const ICONS = {
  history: (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="9" /><polyline points="12 7 12 12 16 14" />
    </svg>
  ),
  admin: (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  ),
  settings: (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="4" y1="21" x2="4" y2="14" /><line x1="4" y1="10" x2="4" y2="3" />
      <line x1="12" y1="21" x2="12" y2="12" /><line x1="12" y1="8" x2="12" y2="3" />
      <line x1="20" y1="21" x2="20" y2="16" /><line x1="20" y1="12" x2="20" y2="3" />
      <line x1="1" y1="14" x2="7" y2="14" /><line x1="9" y1="8" x2="15" y2="8" /><line x1="17" y1="16" x2="23" y2="16" />
    </svg>
  ),
} as const

interface NavButtonProps {
  href: string
  label: string
  icon: keyof typeof ICONS
  active: boolean
}

function NavButton({ href, label, icon, active }: Readonly<NavButtonProps>) {
  return (
    <Link
      href={href}
      className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
        active
          ? 'border-card-border bg-card text-text-primary'
          : 'border-transparent text-text-secondary hover:border-card-border hover:bg-card hover:text-text-primary'
      }`}
    >
      {ICONS[icon]}
      <span className="hidden sm:inline">{label}</span>
    </Link>
  )
}

interface HeaderNavProps {
  isAdmin: boolean
  email: string
}

export function HeaderNav({ isAdmin, email }: Readonly<HeaderNavProps>) {
  const pathname = usePathname()
  const initial = (email[0] ?? '?').toUpperCase()

  return (
    <>
      <div className="flex items-center gap-1.5 justify-self-start">
        <NavButton href="/history" label="Histórico" icon="history" active={pathname.startsWith('/history')} />
        {isAdmin && (
          <NavButton href="/admin" label="Admin" icon="admin" active={pathname.startsWith('/admin')} />
        )}
        <NavButton href="/settings" label="Configurações" icon="settings" active={pathname.startsWith('/settings')} />
      </div>

      <Link
        href="/dashboard"
        className="justify-self-center text-lg font-bold tracking-tight text-text-primary transition-colors hover:text-primary"
      >
        Aether
      </Link>

      <div className="flex items-center justify-self-end">
        <div className="flex items-center gap-2 rounded-full border border-card-border bg-card py-1 pl-1 pr-1">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/15 text-[11px] font-semibold text-primary">
            {initial}
          </span>
          <span className="hidden max-w-[160px] truncate text-xs text-text-secondary md:inline">{email}</span>
          <LogoutButton />
        </div>
      </div>
    </>
  )
}
