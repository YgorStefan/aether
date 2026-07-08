'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import { approveRun } from '@/lib/api'

interface HitlPanelProps {
  runId: string
  skill: string
  params: Record<string, unknown>
}

export function HitlPanel({ runId, skill, params }: Readonly<HitlPanelProps>) {
  const [loading, setLoading] = useState(false)

  async function handleDecision(decision: 'approve' | 'reject') {
    setLoading(true)
    try {
      await approveRun(runId, decision)
    } catch {
      toast.error('Falha ao enviar decisão. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-lg border border-warning/40 bg-warning/5 p-4 space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-warning text-sm font-semibold">⏸ Aprovação necessária</span>
      </div>
      <p className="text-xs text-text-secondary">
        A skill <span className="text-text-primary font-medium">{skill}</span> requer aprovação antes de executar.
      </p>
      {Object.keys(params).length > 0 && (
        <pre className="text-[10px] text-text-muted bg-card rounded p-2 overflow-x-auto">
          {JSON.stringify(params, null, 2)}
        </pre>
      )}
      <div className="flex gap-2">
        <button
          onClick={() => handleDecision('approve')}
          disabled={loading}
          className="flex-1 py-2 rounded text-xs font-semibold bg-success/20 text-success border border-success/40 hover:bg-success/30 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Enviando…' : 'Aprovar'}
        </button>
        <button
          onClick={() => handleDecision('reject')}
          disabled={loading}
          className="flex-1 py-2 rounded text-xs font-semibold bg-error/20 text-error border border-error/40 hover:bg-error/30 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Enviando…' : 'Rejeitar'}
        </button>
      </div>
    </div>
  )
}
