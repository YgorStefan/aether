'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import { approveRun } from '@/lib/api'

interface HitlPanelProps {
  runId: string
  skill: string
  params: Record<string, unknown>
}

export function HitlPanel({ runId, skill, params }: HitlPanelProps) {
  const [loading, setLoading] = useState(false)

  async function handleDecision(decision: 'approve' | 'reject') {
    setLoading(true)
    try {
      await approveRun(runId, decision)
    } catch {
      toast.error('Falha ao enviar decisão. Tente novamente.')
      setLoading(false)
    }
  }

  return (
    <div className="rounded-lg border border-[#fbbf24]/40 bg-[#fbbf24]/5 p-4 space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-[#fbbf24] text-sm font-semibold">⏸ Aprovação necessária</span>
      </div>
      <p className="text-xs text-[#94a3b8]">
        A skill <span className="text-[#e2e8f0] font-medium">{skill}</span> requer aprovação antes de executar.
      </p>
      {Object.keys(params).length > 0 && (
        <pre className="text-[10px] text-[#64748b] bg-[#0a0a0a] rounded p-2 overflow-x-auto">
          {JSON.stringify(params, null, 2)}
        </pre>
      )}
      <div className="flex gap-2">
        <button
          onClick={() => handleDecision('approve')}
          disabled={loading}
          className="flex-1 py-2 rounded text-xs font-semibold bg-[#22c55e]/20 text-[#22c55e] border border-[#22c55e]/40 hover:bg-[#22c55e]/30 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Enviando…' : 'Aprovar'}
        </button>
        <button
          onClick={() => handleDecision('reject')}
          disabled={loading}
          className="flex-1 py-2 rounded text-xs font-semibold bg-[#ef4444]/20 text-[#ef4444] border border-[#ef4444]/40 hover:bg-[#ef4444]/30 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Enviando…' : 'Rejeitar'}
        </button>
      </div>
    </div>
  )
}
