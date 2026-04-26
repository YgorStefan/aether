import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase-server'

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  return (
    <div className="min-h-screen bg-[var(--color-background)]">
      <nav className="border-b border-[var(--color-card-border)] px-6 py-4 flex items-center justify-between">
        <span className="text-sm font-semibold text-[var(--color-text-primary)]">Aether OS</span>
        <span className="text-xs text-[var(--color-text-muted)]">{user.email}</span>
      </nav>
      <main className="p-6">{children}</main>
    </div>
  )
}
