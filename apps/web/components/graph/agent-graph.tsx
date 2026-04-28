'use client'

import {
  ReactFlow,
  Background,
  type NodeTypes,
} from '@xyflow/react'
import { useAgentGraph } from '@/hooks/use-agent-graph'
import { SupervisorNode, WorkerNode, FinalizeNode } from './nodes'
import type { RunEvent } from '@/hooks/use-run-stream'

const nodeTypes: NodeTypes = {
  supervisorNode: SupervisorNode,
  workerNode: WorkerNode,
  finalizeNode: FinalizeNode,
}

interface AgentGraphProps {
  events: RunEvent[]
}

export function AgentGraph({ events }: AgentGraphProps) {
  const { nodes, edges } = useAgentGraph(events)

  return (
    <div className="w-full h-full min-h-[300px] rounded-lg border border-[#1f1f1f] bg-[#0a0a0a] overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        fitView
        fitViewOptions={{ padding: 0.4 }}
        colorMode="dark"
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#1f1f1f" gap={24} />
      </ReactFlow>
    </div>
  )
}
