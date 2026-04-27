'use client'

import { useEffect, useRef, useState } from 'react'
import { createClient } from '@/lib/supabase'

export type RunEventType =
  | 'agent_started'
  | 'task_started'
  | 'task_completed'
  | 'skill_called'
  | 'hitl_required'
  | 'run_completed'
  | 'run_failed'
  | 'budget_warning'

export type RunEvent = {
  run_id: string
  type: RunEventType
  payload: Record<string, unknown>
}

export type StreamStatus = 'idle' | 'connecting' | 'connected' | 'done' | 'error'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
const MAX_BACKOFF_MS = 30_000

export function useRunStream(runId: string | null) {
  const [events, setEvents] = useState<RunEvent[]>([])
  const [status, setStatus] = useState<StreamStatus>('idle')
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const retryRef = useRef(0)

  useEffect(() => {
    if (!runId) return

    let cancelled = false

    async function connect() {
      await Promise.resolve()
      if (cancelled) return
      setStatus('connecting')

      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      if (!session || cancelled) {
        setStatus('error')
        setError('Não autenticado')
        return
      }

      const ac = new AbortController()
      abortRef.current = ac

      try {
        const res = await fetch(`${API_URL}/api/v1/runs/${runId}/stream`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
          signal: ac.signal,
        })
        if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`)

        setStatus('connected')
        retryRef.current = 0

        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done || cancelled) break
          buffer += decoder.decode(value, { stream: true })
          const messages = buffer.split('\n\n')
          buffer = messages.pop() ?? ''

          for (const msg of messages) {
            const dataLine = msg.split('\n').find(l => l.startsWith('data:'))
            if (!dataLine) continue
            try {
              const event: RunEvent = JSON.parse(dataLine.slice(5).trim())
              setEvents(prev => [...prev, event])
              if (event.type === 'run_completed' || event.type === 'run_failed') {
                setStatus('done')
                return
              }
            } catch {
              // ignora JSON malformado
            }
          }
        }
      } catch (err) {
        if (cancelled || (err instanceof Error && err.name === 'AbortError')) return
        const delay = Math.min(1000 * 2 ** retryRef.current, MAX_BACKOFF_MS)
        retryRef.current += 1
        setTimeout(connect, delay)
      }
    }

    connect()

    return () => {
      cancelled = true
      abortRef.current?.abort()
    }
  }, [runId])

  return { events, status, error }
}
