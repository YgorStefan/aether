import { useMemo } from 'react'
import type { Node, Edge } from '@xyflow/react'
import type { RunEvent } from './use-run-stream'
import type { NodeStatus, AgentNodeData } from '@/components/graph/nodes'

export type GraphTaskState = {
  status: NodeStatus
  label: string
  skill?: string
}

export type GraphState = {
  supervisorStatus: NodeStatus
  tasks: GraphTaskState[]
  finalizeStatus: NodeStatus
}

export function buildGraphState(events: RunEvent[]): GraphState {
  let supervisorStatus: NodeStatus = 'idle'
  const tasks: GraphTaskState[] = []
  let finalizeStatus: NodeStatus = 'idle'
  let activeTaskIndex: number | null = null

  for (const event of events) {
    switch (event.type) {
      case 'agent_started':
        supervisorStatus = 'thinking'
        break

      case 'task_started': {
        supervisorStatus = 'done'
        const idx = event.payload.index as number
        while (tasks.length <= idx) tasks.push({ status: 'idle', label: `Worker ${tasks.length + 1}` })
        tasks[idx] = { ...tasks[idx], status: 'thinking', label: `Worker ${idx + 1}` }
        activeTaskIndex = idx
        break
      }

      case 'skill_called':
        if (activeTaskIndex !== null && tasks[activeTaskIndex]) {
          tasks[activeTaskIndex] = {
            ...tasks[activeTaskIndex],
            skill: event.payload.skill as string,
          }
        }
        break

      case 'hitl_required':
        if (activeTaskIndex !== null && tasks[activeTaskIndex]) {
          tasks[activeTaskIndex] = { ...tasks[activeTaskIndex], status: 'hitl_pending' }
        }
        break

      case 'hitl_resolved':
        if (activeTaskIndex !== null && tasks[activeTaskIndex]?.status === 'hitl_pending') {
          tasks[activeTaskIndex] = { ...tasks[activeTaskIndex], status: 'thinking' }
        }
        break

      case 'task_completed': {
        const idx = event.payload.index as number
        const s = event.payload.status as string
        if (tasks[idx]) {
          tasks[idx] = { ...tasks[idx], status: s === 'done' ? 'done' : 'failed' }
        }
        activeTaskIndex = null
        break
      }

      case 'run_completed':
        finalizeStatus = 'done'
        break

      case 'run_failed':
        finalizeStatus = 'failed'
        break
    }
  }

  return { supervisorStatus, tasks, finalizeStatus }
}

const NODE_SPACING_X = 220
const NODE_Y = 60

export function useAgentGraph(events: RunEvent[]): { nodes: Node<AgentNodeData>[]; edges: Edge[] } {
  return useMemo(() => {
    const { supervisorStatus, tasks, finalizeStatus } = buildGraphState(events)

    const nodes: Node<AgentNodeData>[] = []
    const edges: Edge[] = []

    nodes.push({
      id: 'supervisor',
      type: 'supervisorNode',
      position: { x: 0, y: NODE_Y },
      data: { label: 'Supervisor', status: supervisorStatus },
    })

    tasks.forEach((task, i) => {
      const x = NODE_SPACING_X * (i + 1)
      nodes.push({
        id: `worker-${i}`,
        type: 'workerNode',
        position: { x, y: NODE_Y },
        data: { label: task.label, status: task.status, skill: task.skill },
      })

      const source = i === 0 ? 'supervisor' : `worker-${i - 1}`
      edges.push({
        id: `e-${source}-worker-${i}`,
        source,
        target: `worker-${i}`,
        animated: task.status === 'thinking' || task.status === 'hitl_pending',
        style: { stroke: '#64748b' },
      })
    })

    if (finalizeStatus !== 'idle' || tasks.length > 0) {
      const finalizeX = NODE_SPACING_X * (tasks.length + 1)
      nodes.push({
        id: 'finalize',
        type: 'finalizeNode',
        position: { x: finalizeX, y: NODE_Y },
        data: { label: 'Resultado', status: finalizeStatus },
      })

      const lastSource = tasks.length > 0 ? `worker-${tasks.length - 1}` : 'supervisor'
      edges.push({
        id: 'e-last-finalize',
        source: lastSource,
        target: 'finalize',
        animated: finalizeStatus === 'thinking',
        style: { stroke: '#64748b' },
      })
    }

    return { nodes, edges }
  }, [events])
}
