import { notFound } from 'next/navigation'
import { createClient } from '@/lib/supabase-server'
import { RunView } from './run-view'
import type { RunEvent } from '@/hooks/use-run-stream'

interface PageProps {
  params: Promise<{ id: string }>
}

export default async function RunPage({ params }: Readonly<PageProps>) {
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

  // Carrega eventos já persistidos mesmo para runs ainda em andamento, para não
  // perder o histórico ao recarregar a página no meio de uma execução (o SSE só
  // emite eventos novos a partir do momento em que a conexão é aberta).
  const { data: dbEvents } = await supabase
    .from('run_events')
    .select('run_id, type, agent_name, tokens_used, payload')
    .eq('run_id', id)
    .order('created_at')
  const initialEvents = (dbEvents ?? []) as RunEvent[]

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold text-text-primary">Detalhes do Run</h1>
      <RunView
        runId={run.id}
        objective={run.objective}
        initialStatus={run.status}
        initialEvents={initialEvents}
      />
    </div>
  )
}
