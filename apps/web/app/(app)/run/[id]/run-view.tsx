'use client'

import { useEffect } from 'react'
import { toast } from 'sonner'
import { useRunStream } from '@/hooks/use-run-stream'
import { MessageList } from '@/components/chat/message-list'
import { ChatErrorBoundary } from '@/components/chat/chat-error-boundary'
import { StatusBadge } from '@/components/run/status-badge'

interface RunViewProps {
  runId: string
  objective: string
  initialStatus: string
}

export function RunView({ runId, objective, initialStatus }: RunViewProps) {
  const { events, status } = useRunStream(runId)

  const lastEvent = events[events.length - 1]

  const currentStatus =
    lastEvent?.type === 'run_completed' ? 'completed' :
    lastEvent?.type === 'run_failed' ? 'failed' :
    status === 'connected' || status === 'connecting' ? 'running' :
    initialStatus

  useEffect(() => {
    if (!lastEvent) return
    if (lastEvent.type === 'run_completed') toast.success('Run concluído!')
    if (lastEvent.type === 'run_failed') toast.error(`Run falhou: ${String(lastEvent.payload.error ?? '')}`)
    if (lastEvent.type === 'hitl_required') {
      toast.warning(`Aprovação necessária: ${String(lastEvent.payload.action ?? '')}`)
    }
  }, [lastEvent])

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-3">
        <h2 className="flex-1 text-sm text-[var(--color-text-secondary)] line-clamp-2">{objective}</h2>
        <StatusBadge status={currentStatus} />
      </div>
      <ChatErrorBoundary>
        <MessageList events={events} />
      </ChatErrorBoundary>
    </div>
  )
}
