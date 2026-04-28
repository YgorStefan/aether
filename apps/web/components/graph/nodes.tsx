'use client'

import { Handle, Position, type NodeProps } from '@xyflow/react'
import { motion } from 'framer-motion'

export type NodeStatus = 'idle' | 'thinking' | 'done' | 'failed' | 'hitl_pending'

export type AgentNodeData = {
  label: string
  status: NodeStatus
  skill?: string
}

const STATUS_COLORS: Record<NodeStatus, string> = {
  idle: '#1f1f1f',
  thinking: '#3b82f6',
  done: '#22c55e',
  failed: '#ef4444',
  hitl_pending: '#fbbf24',
}

const SUPERVISOR_COLORS: Record<NodeStatus, string> = {
  ...STATUS_COLORS,
  thinking: '#a855f7',
}

function glowAnimation(status: NodeStatus, color: string) {
  if (status === 'thinking' || status === 'hitl_pending') {
    return {
      animate: {
        boxShadow: [`0 0 4px ${color}`, `0 0 18px ${color}`, `0 0 4px ${color}`],
      },
      transition: { duration: 1.5, repeat: Infinity, ease: 'easeInOut' as const },
    }
  }
  return {
    animate: { boxShadow: status === 'done' || status === 'failed' ? `0 0 8px ${color}` : '0 0 0px transparent' },
    transition: { duration: 0.3 },
  }
}

export function SupervisorNode({ data }: NodeProps) {
  const d = data as AgentNodeData
  const color = SUPERVISOR_COLORS[d.status]
  const { animate, transition } = glowAnimation(d.status, color)

  return (
    <>
      <Handle type="source" position={Position.Right} />
      <motion.div
        animate={animate}
        transition={transition}
        style={{ borderColor: color }}
        className="px-4 py-3 rounded-lg border-2 bg-[#0a0a0a] min-w-[120px] text-center"
      >
        <p className="text-xs font-semibold text-[#a855f7]">SUPERVISOR</p>
        <p className="text-xs text-[#e2e8f0] mt-1">{d.label}</p>
        {d.status === 'thinking' && (
          <p className="text-[10px] text-[#94a3b8] mt-1">Planejando…</p>
        )}
      </motion.div>
    </>
  )
}

export function WorkerNode({ data }: NodeProps) {
  const d = data as AgentNodeData
  const color = STATUS_COLORS[d.status]
  const { animate, transition } = glowAnimation(d.status, color)

  return (
    <>
      <Handle type="target" position={Position.Left} />
      <motion.div
        animate={animate}
        transition={transition}
        style={{ borderColor: color }}
        className="px-4 py-3 rounded-lg border-2 bg-[#0a0a0a] min-w-[140px] text-center"
      >
        <p className="text-xs font-semibold text-[#3b82f6]">WORKER</p>
        <p className="text-xs text-[#e2e8f0] mt-1">{d.label}</p>
        {d.skill && d.status === 'thinking' && (
          <p className="text-[10px] text-[#94a3b8] mt-1">→ {d.skill}</p>
        )}
        {d.status === 'hitl_pending' && (
          <p className="text-[10px] text-[#fbbf24] mt-1">⏸ Aguardando aprovação</p>
        )}
      </motion.div>
      <Handle type="source" position={Position.Right} />
    </>
  )
}

export function FinalizeNode({ data }: NodeProps) {
  const d = data as AgentNodeData
  const color = STATUS_COLORS[d.status]
  const { animate, transition } = glowAnimation(d.status, color)

  return (
    <>
      <Handle type="target" position={Position.Left} />
      <motion.div
        animate={animate}
        transition={transition}
        style={{ borderColor: color }}
        className="px-4 py-3 rounded-lg border-2 bg-[#0a0a0a] min-w-[120px] text-center"
      >
        <p className="text-xs font-semibold text-[#22c55e]">FINALIZAR</p>
        <p className="text-xs text-[#e2e8f0] mt-1">{d.label}</p>
      </motion.div>
    </>
  )
}
