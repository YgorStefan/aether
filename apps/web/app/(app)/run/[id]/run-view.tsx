'use client'

import { useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import { useRunStream, type RunEvent, type StreamStatus } from '@/hooks/use-run-stream'
import { MessageList } from '@/components/chat/message-list'
import { ChatErrorBoundary } from '@/components/chat/chat-error-boundary'
import { StatusBadge } from '@/components/run/status-badge'
import { BudgetProgressBar } from '@/components/run/budget-progress-bar'
import { AgentGraph } from '@/components/graph/agent-graph'
import { HitlPanel } from '@/components/hitl/hitl-panel'
import { BackButton } from '@/components/ui/back-button'

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

const USAGE_EVENT_TYPES = new Set<RunEvent['type']>([
  'task_completed',
  'run_completed',
  'run_failed',
  'budget_exceeded',
])

function applyAgentStartedEvent(acc: TokenState, payload: Record<string, unknown>): void {
  if (typeof payload.budget_limit === 'number') acc.budgetLimit = payload.budget_limit
  if (typeof payload.langsmith_enabled === 'boolean') acc.langsmithEnabled = payload.langsmith_enabled
}

function applyUsageEvent(acc: TokenState, payload: Record<string, unknown>): void {
  if (typeof payload.total_input_tokens === 'number') acc.totalInputTokens = payload.total_input_tokens
  if (typeof payload.total_output_tokens === 'number') acc.totalOutputTokens = payload.total_output_tokens
  if (typeof payload.cost_usd === 'number') acc.costUsd = payload.cost_usd
}

function deriveTokenState(events: RunEvent[]): TokenState {
  const state: TokenState = {
    budgetLimit: 10000,
    totalInputTokens: 0,
    totalOutputTokens: 0,
    costUsd: 0,
    langsmithEnabled: false,
  }

  for (const e of events) {
    if (e.type === 'agent_started') applyAgentStartedEvent(state, e.payload)
    if (USAGE_EVENT_TYPES.has(e.type)) applyUsageEvent(state, e.payload)
  }

  return state
}

function deriveCurrentStatus(
  lastEvent: RunEvent | undefined,
  status: StreamStatus,
  initialStatus: string
): string {
  if (lastEvent?.type === 'run_completed') return 'completed'
  if (lastEvent?.type === 'run_failed') return 'failed'
  if (status === 'connected' || status === 'connecting') return 'running'
  return initialStatus
}

function payloadText(value: unknown): string {
  if (typeof value === 'string') return value
  if (value == null) return ''
  return JSON.stringify(value)
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

export function RunView({ runId, objective, initialStatus, initialEvents = [] }: Readonly<RunViewProps>) {
  const { events, status } = useRunStream(runId, { initialEvents, initialStatus })
  const [showGraph, setShowGraph] = useState(true)

  const lastEvent = events.at(-1)

  const currentStatus = deriveCurrentStatus(lastEvent, status, initialStatus)

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
    if (lastEvent.type === 'run_failed') toast.error(`Run falhou: ${payloadText(lastEvent.payload.error)}`)
    if (lastEvent.type === 'hitl_required') {
      toast.warning(`Aprovação necessária: ${payloadText(lastEvent.payload.skill)}`)
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
      <div className="flex items-center gap-3 shrink-0 flex-wrap">
        <BackButton />
        <h2 className="flex-1 text-sm text-text-secondary line-clamp-1 min-w-0">
          {objective}
        </h2>
        <StatusBadge status={currentStatus} />
        {totalTokens > 0 && (
          <span className="text-xs text-text-secondary whitespace-nowrap tabular-nums">
            {totalTokens.toLocaleString('pt-BR')} tokens · ${tokenState.costUsd.toFixed(4)}
          </span>
        )}
        <button
          onClick={() => setShowGraph(prev => !prev)}
          className="md:hidden text-xs text-text-secondary border border-card-border rounded px-2 py-1 hover:bg-card-border transition-colors"
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
            <div className="rounded-lg border border-card-border bg-card p-3">
              <p className="text-xs text-text-muted mb-2 font-medium">Tokens por agente</p>
              <div className="space-y-1">
                {agentTokenTable.map(({ agent, tokens }) => (
                  <div key={agent} className="flex justify-between text-xs">
                    <span className="text-text-secondary">{agent}</span>
                    <span className="text-text-muted tabular-nums">{tokens.toLocaleString('pt-BR')}</span>
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
      <div className="flex items-center gap-4 shrink-0 pt-1">
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
            className="text-xs text-text-muted hover:text-text-secondary transition-colors whitespace-nowrap"
          >
            LangSmith ↗
          </a>
        )}
      </div>
    </div>
  )
}
