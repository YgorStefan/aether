import { createClient } from '@/lib/supabase'
import type { RunEvent } from '@/hooks/use-run-stream'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function authHeaders(): Promise<Record<string, string>> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) throw new Error('Não autenticado')
  return { Authorization: `Bearer ${session.access_token}` }
}

export type SkillMetadata = {
  name: string
  description: string
  parameters_schema: Record<string, unknown>
  requires_approval: boolean
}

export type Run = {
  id: string
  objective: string
  status: 'created' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'
  created_at: string
  total_tokens: number
  cost_usd: number
}

export async function createRun(objective: string): Promise<{ run_id: string }> {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/v1/runs`, {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ objective }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getSkills(): Promise<SkillMetadata[]> {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/v1/skills`, { headers })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function approveRun(runId: string, decision: 'approve' | 'reject'): Promise<void> {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/v1/runs/${runId}/approve`, {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision }),
  })
  if (!res.ok) throw new Error(await res.text())
}

export async function getRunEvents(runId: string): Promise<RunEvent[]> {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/v1/runs/${runId}/events`, { headers })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

// Re-export RunEvent type alinhado com o hook
export type { RunEvent } from '@/hooks/use-run-stream'
