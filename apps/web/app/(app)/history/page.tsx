import { createClient } from '@/lib/supabase-server'
import { RunCard } from '@/components/run/run-card'
import type { Run } from '@/lib/api'

export default async function HistoryPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  const { data: runs } = await supabase
    .from('runs')
    .select('id, objective, status, created_at, total_tokens, cost_usd')
    .eq('user_id', user!.id)
    .order('created_at', { ascending: false })

  const typedRuns = (runs ?? []) as Run[]

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">Histórico</h1>
      {typedRuns.length === 0 ? (
        <p className="text-sm text-[var(--color-text-muted)]">Nenhum run ainda.</p>
      ) : (
        <div className="space-y-3">
          {typedRuns.map(run => (
            <RunCard key={run.id} run={run} />
          ))}
        </div>
      )}
    </div>
  )
}
