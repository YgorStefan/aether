import { notFound } from 'next/navigation'
import { createClient } from '@/lib/supabase-server'
import { RunView } from './run-view'

interface PageProps {
  params: Promise<{ id: string }>
}

export default async function RunPage({ params }: PageProps) {
  const { id } = await params
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  const { data: run } = await supabase
    .from('runs')
    .select('id, objective, status')
    .eq('id', id)
    .eq('user_id', user!.id)
    .single()

  if (!run) notFound()

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">Run Detail</h1>
      <RunView runId={run.id} objective={run.objective} initialStatus={run.status} />
    </div>
  )
}
