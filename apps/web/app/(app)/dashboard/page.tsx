import { createClient } from '@/lib/supabase-server'
import { DashboardClient } from './dashboard-client'
import type { Run } from '@/lib/api'

export default async function DashboardPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  const { data: runs } = await supabase
    .from('runs')
    .select('id, objective, status, created_at, total_tokens, cost_usd')
    .eq('user_id', user!.id)
    .order('created_at', { ascending: false })
    .limit(5)

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">Dashboard</h1>
      <DashboardClient initialRuns={(runs ?? []) as Run[]} />
    </div>
  )
}
