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

export function DashboardClient({ initialRuns }: { initialRuns: Run[] }) {
  const router = useRouter()
  const [runs, setRuns] = useState<Run[]>(initialRuns)

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
                <RunCard key={run.id} run={run} />
              ))}
            </div>
          )}
        </SpotlightCard>
      </BentoItem>
    </BentoGrid>
  )
}
