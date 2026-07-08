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

// Status vem do banco em maiúsculas (CREATED, RUNNING, PAUSED, COMPLETED, FAILED,
// CANCELLED), mas a UI otimista do dashboard usa valores transitórios em minúsculas
// antes da run real chegar — StatusBadge normaliza com toLowerCase() em ambos os casos.
export type Run = {
  id: string
  objective: string
  status: string
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

export type UserSettings = {
  provider: 'gemini' | null
  api_key_set: boolean
  api_key_masked: string | null
}

export async function getSettings(): Promise<UserSettings> {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/v1/settings`, { headers })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function updateSettings(provider: 'gemini', api_key: string): Promise<void> {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/v1/settings`, {
    method: 'PUT',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider, api_key }),
  })
  if (!res.ok) throw new Error(await res.text())
}

export async function deleteAccount(): Promise<void> {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/v1/account`, {
    method: 'DELETE',
    headers,
  })
  if (!res.ok) throw new Error(await res.text())
}

export type Me = { email: string; role: 'user' | 'admin' }

export async function getMe(): Promise<Me> {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/v1/me`, { headers })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export type AdminUser = {
  user_id: string
  email: string
  role: 'user' | 'admin'
  created_at: string
  run_count: number
}

export async function getAdminUsers(): Promise<AdminUser[]> {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/v1/admin/users`, { headers })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export type AdminRun = {
  id: string
  user_id: string
  user_email: string
  objective: string
  status: string
  total_tokens: number
  cost_usd: number
  created_at: string
}

export async function getAdminRuns(): Promise<AdminRun[]> {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/v1/admin/runs`, { headers })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

// Re-export RunEvent type alinhado com o hook
export type { RunEvent } from '@/hooks/use-run-stream'
