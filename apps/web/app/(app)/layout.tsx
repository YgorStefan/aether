import Link from 'next/link'
import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase-server'
import { LogoutButton } from '@/components/ui/logout-button'

export default async function AppLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  const { data: profile } = await supabase
    .from('profiles')
    .select('role')
    .eq('user_id', user.id)
    .single()
  const isAdmin = profile?.role === 'admin'

  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b border-card-border px-6 py-4 flex items-center justify-between">
        <span className="text-sm font-semibold text-text-primary">Aether</span>
        <div className="flex items-center gap-3">
          <span className="text-xs text-text-muted">{user.email}</span>
          <Link href="/history" className="text-xs text-text-muted hover:text-text-primary transition-colors">
            Histórico
          </Link>
          {isAdmin && (
            <Link href="/admin" className="text-xs text-text-muted hover:text-text-primary transition-colors">
              Admin
            </Link>
          )}
          <Link href="/settings" className="text-xs text-text-muted hover:text-text-primary transition-colors">
            Configurações
          </Link>
          <LogoutButton />
        </div>
      </nav>
      <main className="p-6">{children}</main>
    </div>
  )
}
