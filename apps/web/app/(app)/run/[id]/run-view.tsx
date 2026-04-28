'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { toast } from 'sonner'
import { useRunStream, type RunEvent } from '@/hooks/use-run-stream'
import { MessageList } from '@/components/chat/message-list'
import { ChatErrorBoundary } from '@/components/chat/chat-error-boundary'
import { StatusBadge } from '@/components/run/status-badge'
import { BudgetProgressBar } from '@/components/run/budget-progress-bar'
import { AgentGraph } from '@/components/graph/agent-graph'
import { HitlPanel } from '@/components/hitl/hitl-panel'

interface RunViewProps {
  runId: string
  objective: string
  initialStatus: string
  initialEvents?: RunEvent[]
}

interface TokenState {
  budgetLimit: number
  totalInputTokens: number
  totalOutputTokens: number
  costUsd: number
  langsmithEnabled: boolean
}

function deriveTokenState(events: RunEvent[]): TokenState {
  let budgetLimit = 10000
  let totalInputTokens = 0
  let totalOutputTokens = 0
  let costUsd = 0
  let langsmithEnabled = false

  for (const e of events) {
    if (e.type === 'agent_started') {
      if (typeof e.payload.budget_limit === 'number') budgetLimit = e.payload.budget_limit
      if (typeof e.payload.langsmith_enabled === 'boolean') langsmithEnabled = e.payload.langsmith_enabled
    }
    if (
      e.type === 'task_completed' ||
      e.type === 'run_completed' ||
      e.type === 'run_failed' ||
      e.type === 'budget_exceeded'
    ) {
      if (typeof e.payload.total_input_tokens === 'number') totalInputTokens = e.payload.total_input_tokens
      if (typeof e.payload.total_output_tokens === 'number') totalOutputTokens = e.payload.total_output_tokens
      if (typeof e.payload.cost_usd === 'number') costUsd = e.payload.cost_usd
    }
  }

  return { budgetLimit, totalInputTokens, totalOutputTokens, costUsd, langsmithEnabled }
}

function buildAgentTokenTable(events: RunEvent[]): Array<{ agent: string; tokens: number }> {
  const totals = new Map<string, number>()
  for (const e of events) {
    if (
      (e.type === 'agent_started' || e.type === 'task_completed') &&
      (e.tokens_used ?? 0) > 0
    ) {
      const key = e.agent_name ?? 'unknown'
      totals.set(key, (totals.get(key) ?? 0) + (e.tokens_used ?? 0))
    }
  }
  return Array.from(totals.entries()).map(([agent, tokens]) => ({ agent, tokens }))
}

export function RunView({ runId, objective, initialStatus, initialEvents = [] }: RunViewProps) {
  const { events, status } = useRunStream(runId, { initialEvents, initialStatus })
  const [showGraph, setShowGraph] = useState(true)

  const lastEvent = events[events.length - 1]

  const currentStatus =
    lastEvent?.type === 'run_completed' ? 'completed' :
    lastEvent?.type === 'run_failed' ? 'failed' :
    status === 'connected' || status === 'connecting' ? 'running' :
    initialStatus

  const pendingHitlEvent = useMemo(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const e = events[i]
      if (e.type === 'hitl_required') return e
      if (e.type === 'hitl_resolved') return null
    }
    return null
  }, [events])

  const tokenState = useMemo(() => deriveTokenState(events), [events])
  const agentTokenTable = useMemo(() => buildAgentTokenTable(events), [events])
  const totalTokens = tokenState.totalInputTokens + tokenState.totalOutputTokens

  useEffect(() => {
    if (!lastEvent) return
    if (lastEvent.type === 'run_completed') toast.success('Run concluído!')
    if (lastEvent.type === 'run_failed') toast.error(`Run falhou: ${String(lastEvent.payload.error ?? '')}`)
    if (lastEvent.type === 'hitl_required') {
      toast.warning(`Aprovação necessária: ${String(lastEvent.payload.skill ?? '')}`)
    }
    if (lastEvent.type === 'budget_warning') {
      toast.warning('80% do budget consumido')
    }
    if (lastEvent.type === 'budget_exceeded') {
      toast.error('Budget esgotado — run interrompido')
    }
  }, [lastEvent])

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Top bar */}
      <div className="flex items-center gap-3 flex-shrink-0 flex-wrap">
        <Link
          href="/dashboard"
          className="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors flex items-center gap-1 whitespace-nowrap"
        >
          ← Voltar
        </Link>
        <h2 className="flex-1 text-sm text-[var(--color-text-secondary)] line-clamp-1 min-w-0">
          {objective}
        </h2>
        <StatusBadge status={currentStatus} />
        {totalTokens > 0 && (
          <span className="text-xs text-[#94a3b8] whitespace-nowrap tabular-nums">
            {totalTokens.toLocaleString('pt-BR')} tokens · ${tokenState.costUsd.toFixed(4)}
          </span>
        )}
        <button
          onClick={() => setShowGraph(prev => !prev)}
          className="md:hidden text-xs text-[#94a3b8] border border-[#1f1f1f] rounded px-2 py-1 hover:bg-[#1f1f1f] transition-colors"
        >
          {showGraph ? 'Logs' : 'Grafo'}
        </button>
      </div>

      {/* Main content: 60/40 split no desktop, toggle no mobile */}
      <div className="flex flex-1 gap-4 min-h-0">
        {/* Graph panel — 60% no desktop, toggle no mobile */}
        <div className={`${showGraph ? 'flex' : 'hidden'} md:flex flex-col md:w-[60%] min-h-[300px]`}>
          <ChatErrorBoundary>
            <AgentGraph events={events} />
          </ChatErrorBoundary>
        </div>

        {/* Logs + HITL panel — 40% no desktop, toggle no mobile */}
        <div className={`${showGraph ? 'hidden' : 'flex'} md:flex flex-col md:w-[40%] gap-3 overflow-y-auto`}>
          {pendingHitlEvent && (
            <HitlPanel
              runId={runId}
              skill={pendingHitlEvent.payload.skill as string}
              params={(pendingHitlEvent.payload.params ?? {}) as Record<string, unknown>}
            />
          )}

          {/* Tabela de tokens por agente */}
          {agentTokenTable.length > 0 && (
            <div className="rounded-lg border border-[#1f1f1f] bg-[#0a0a0a] p-3">
              <p className="text-xs text-[#64748b] mb-2 font-medium">Tokens por agente</p>
              <div className="space-y-1">
                {agentTokenTable.map(({ agent, tokens }) => (
                  <div key={agent} className="flex justify-between text-xs">
                    <span className="text-[#94a3b8]">{agent}</span>
                    <span className="text-[#64748b] tabular-nums">{tokens.toLocaleString('pt-BR')}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <ChatErrorBoundary>
            <MessageList events={events} />
          </ChatErrorBoundary>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="flex items-center gap-4 flex-shrink-0 pt-1">
        <div className="flex-1 min-w-0">
          <BudgetProgressBar
            totalTokens={totalTokens}
            budgetLimit={tokenState.budgetLimit}
            costUsd={tokenState.costUsd}
          />
        </div>
        {tokenState.langsmithEnabled && (
          <a
            href="https://smith.langchain.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-[#64748b] hover:text-[#94a3b8] transition-colors whitespace-nowrap"
          >
            LangSmith ↗
          </a>
        )}
      </div>
    </div>
  )
}
