import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase-server'
import { HeaderNav } from './header-nav'

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
      <nav className="grid grid-cols-[1fr_auto_1fr] items-center gap-4 border-b border-card-border px-6 py-3">
        <HeaderNav isAdmin={isAdmin} email={user.email ?? ''} />
      </nav>
      <main className="p-6">{children}</main>
    </div>
  )
}
