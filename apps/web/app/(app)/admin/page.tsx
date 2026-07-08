import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase-server'
import { AdminView } from './admin-view'

export default async function AdminPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  const { data: profile } = await supabase
    .from('profiles')
    .select('role')
    .eq('user_id', user!.id)
    .single()

  if (profile?.role !== 'admin') {
    redirect('/dashboard')
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold text-text-primary">Painel Admin</h1>
      <AdminView />
    </div>
  )
}
