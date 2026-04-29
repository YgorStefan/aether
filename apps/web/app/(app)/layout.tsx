import Link from 'next/link'
import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase-server'
import { LogoutButton } from '@/components/ui/logout-button'

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  return (
    <div className="min-h-screen bg-[var(--color-background)]">
      <nav className="border-b border-[var(--color-card-border)] px-6 py-4 flex items-center justify-between">
        <span className="text-sm font-semibold text-[var(--color-text-primary)]">Aether</span>
        <div className="flex items-center gap-3">
          <span className="text-xs text-[var(--color-text-muted)]">{user.email}</span>
          <Link href="/settings" className="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors">
            Configurações
          </Link>
          <LogoutButton />
        </div>
      </nav>
      <main className="p-6">{children}</main>
    </div>
  )
}
