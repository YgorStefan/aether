'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { toast } from 'sonner'
import { useRunStream } from '@/hooks/use-run-stream'
import { MessageList } from '@/components/chat/message-list'
import { ChatErrorBoundary } from '@/components/chat/chat-error-boundary'
import { StatusBadge } from '@/components/run/status-badge'
import { AgentGraph } from '@/components/graph/agent-graph'
import { HitlPanel } from '@/components/hitl/hitl-panel'

interface RunViewProps {
  runId: string
  objective: string
  initialStatus: string
}

export function RunView({ runId, objective, initialStatus }: RunViewProps) {
  const { events, status } = useRunStream(runId)
  const [showGraph, setShowGraph] = useState(true)

  const lastEvent = events[events.length - 1]

  const currentStatus =
    lastEvent?.type === 'run_completed' ? 'completed' :
    lastEvent?.type === 'run_failed' ? 'failed' :
    status === 'connected' || status === 'connecting' ? 'running' :
    initialStatus

  // Encontrar HITL pendente: escaneia do fim para o início, para do primeiro hitl_required ou hitl_resolved
  const pendingHitlEvent = useMemo(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const e = events[i]
      if (e.type === 'hitl_required') return e
      if (e.type === 'hitl_resolved') return null
    }
    return null
  }, [events])

  useEffect(() => {
    if (!lastEvent) return
    if (lastEvent.type === 'run_completed') toast.success('Run concluído!')
    if (lastEvent.type === 'run_failed') toast.error(`Run falhou: ${String(lastEvent.payload.error ?? '')}`)
    if (lastEvent.type === 'hitl_required') {
      toast.warning(`Aprovação necessária: ${String(lastEvent.payload.skill ?? '')}`)
    }
  }, [lastEvent])

  return (
    <div className="flex flex-col h-full gap-4">
      {/* Top bar */}
      <div className="flex items-center gap-3 flex-shrink-0">
        <Link
          href="/dashboard"
          className="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors flex items-center gap-1 whitespace-nowrap"
        >
          ← Voltar
        </Link>
        <h2 className="flex-1 text-sm text-[var(--color-text-secondary)] line-clamp-1">{objective}</h2>
        <StatusBadge status={currentStatus} />
        {/* Mobile toggle */}
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
          <ChatErrorBoundary>
            <MessageList events={events} />
          </ChatErrorBoundary>
        </div>
      </div>
    </div>
  )
}
