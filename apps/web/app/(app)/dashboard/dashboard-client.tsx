'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { BentoGrid, BentoItem } from '@/components/bento/bento-grid'
import { SpotlightCard } from '@/components/ui/spotlight-card'
import { ChatInput } from '@/components/chat/chat-input'
import { ChatErrorBoundary } from '@/components/chat/chat-error-boundary'
import { SkillsCatalog } from '@/components/skills/skills-catalog'
import { RunCard } from '@/components/run/run-card'
import { createRun, type Run } from '@/lib/api'
import { createClient } from '@/lib/supabase'

export function DashboardClient({ initialRuns }: { initialRuns: Run[] }) {
  const router = useRouter()
  const [runs, setRuns] = useState<Run[]>(initialRuns)

  async function handleDelete(id: string) {
    setRuns(prev => prev.filter(r => r.id !== id))
    try {
      const supabase = createClient()
      await supabase.from('runs').delete().eq('id', id)
    } catch {
      toast.error('Erro ao deletar run')
    }
  }

  async function handleSubmit(objective: string) {
    const optimisticId = `optimistic-${Date.now()}`
    const optimisticRun: Run = {
      id: optimisticId,
      objective,
      status: 'created',
      created_at: new Date().toISOString(),
      total_tokens: 0,
      cost_usd: 0,
    }
    setRuns(prev => [optimisticRun, ...prev].slice(0, 5))

    try {
      const { run_id } = await createRun(objective)
      setRuns(prev =>
        prev.map(r => r.id === optimisticId ? { ...optimisticRun, id: run_id, status: 'running' } : r)
      )
      toast.success('Run iniciado!')
      router.push(`/run/${run_id}`)
    } catch (err) {
      setRuns(prev => prev.filter(r => r.id !== optimisticId))
      toast.error(`Erro ao criar run: ${err instanceof Error ? err.message : 'Tente novamente'}`)
    }
  }

  return (
    <BentoGrid>
      <BentoItem colSpan={2}>
        <SpotlightCard className="p-6">
          <p className="text-sm text-[var(--color-text-muted)] mb-4">Novo objetivo</p>
          <ChatErrorBoundary>
            <ChatInput onSubmit={handleSubmit} />
          </ChatErrorBoundary>
        </SpotlightCard>
      </BentoItem>

      <BentoItem>
        <SpotlightCard className="p-6 h-full">
          <p className="text-sm text-[var(--color-text-muted)] mb-3">Skills disponíveis</p>
          <SkillsCatalog />
        </SpotlightCard>
      </BentoItem>

      <BentoItem colSpan={3}>
        <SpotlightCard className="p-6">
          <p className="text-sm text-[var(--color-text-muted)] mb-3">Runs recentes</p>
          {runs.length === 0 ? (
            <p className="text-xs text-[var(--color-text-muted)]">Nenhum run ainda. Comece acima!</p>
          ) : (
            <div className="space-y-2">
              {runs.slice(0, 5).map(run => (
                <div key={run.id} className="flex items-center gap-2">
                  <div className="flex-1 min-w-0">
                    <RunCard run={run} />
                  </div>
                  <button
                    onClick={() => handleDelete(run.id)}
                    aria-label="Deletar run"
                    className="shrink-0 p-1.5 rounded text-[var(--color-text-muted)] hover:text-[var(--color-error)] hover:bg-red-950 transition-colors"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </SpotlightCard>
      </BentoItem>
    </BentoGrid>
  )
}
