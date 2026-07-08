'use client'

import { useEffect, useRef, useState } from 'react'
import { createClient } from '@/lib/supabase'

export type RunEventType =
  | 'agent_started'
  | 'task_started'
  | 'task_completed'
  | 'skill_called'
  | 'skill_result'
  | 'hitl_required'
  | 'hitl_resolved'
  | 'run_completed'
  | 'run_failed'
  | 'run_cancelled'
  | 'budget_warning'
  | 'budget_exceeded'

export type RunEvent = {
  run_id: string
  type: RunEventType
  agent_name?: string | null
  tokens_used?: number
  payload: Record<string, unknown>
}

export type StreamStatus = 'idle' | 'connecting' | 'connected' | 'done' | 'error'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
const MAX_BACKOFF_MS = 30_000
const TERMINAL_STATUSES = new Set(['completed', 'failed', 'cancelled', 'COMPLETED', 'FAILED', 'CANCELLED'])

function isTerminalEvent(event: RunEvent): boolean {
  return event.type === 'run_completed' || event.type === 'run_failed'
}

function parseSseChunk(buffer: string): { events: RunEvent[]; remainder: string } {
  const messages = buffer.split('\n\n')
  const remainder = messages.pop() ?? ''
  const events: RunEvent[] = []

  for (const msg of messages) {
    const dataLine = msg.split('\n').find(l => l.startsWith('data:'))
    if (!dataLine) continue
    try {
      events.push(JSON.parse(dataLine.slice(5).trim()))
    } catch {
      // ignora JSON malformado
    }
  }

  return { events, remainder }
}

// sse_starlette termina cada evento com "\r\n\r\n" (CRLF); normaliza para "\n\n" antes
// de dividir, senão o split em parseSseChunk nunca encontra um separador e nenhum
// evento chega a ser processado.
async function readEventStream(
  body: ReadableStream<Uint8Array>,
  onEvent: (event: RunEvent) => void,
  isCancelled: () => boolean
): Promise<void> {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done || isCancelled()) return

    buffer += decoder.decode(value, { stream: true }).replaceAll('\r\n', '\n')
    const parsed = parseSseChunk(buffer)
    buffer = parsed.remainder

    for (const event of parsed.events) {
      onEvent(event)
      if (isTerminalEvent(event)) return
    }
  }
}

export function useRunStream(
  runId: string | null,
  options: { initialEvents?: RunEvent[]; initialStatus?: string } = {}
) {
  const { initialEvents = [], initialStatus = '' } = options
  const isTerminal = TERMINAL_STATUSES.has(initialStatus)

  const [events, setEvents] = useState<RunEvent[]>(initialEvents)
  const [status, setStatus] = useState<StreamStatus>(isTerminal ? 'done' : 'idle')
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const retryRef = useRef(0)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const eventsRef = useRef<RunEvent[]>(initialEvents)

  useEffect(() => {
    if (!runId || isTerminal) return

    retryRef.current = 0
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

        let terminal = false
        await readEventStream(
          res.body,
          (event) => {
            eventsRef.current = [...eventsRef.current, event]
            setEvents(eventsRef.current)
            if (isTerminalEvent(event)) terminal = true
          },
          () => cancelled
        )
        if (terminal) setStatus('done')
      } catch (err) {
        if (cancelled || (err instanceof Error && err.name === 'AbortError')) return
        const delay = Math.min(1000 * 2 ** retryRef.current, MAX_BACKOFF_MS)
        retryRef.current += 1
        timerRef.current = setTimeout(connect, delay)
      }
    }

    connect()

    return () => {
      cancelled = true
      abortRef.current?.abort()
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [runId, isTerminal])

  return { events, status, error }
}
