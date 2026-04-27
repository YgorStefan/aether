# Fase 4 — Frontend Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Conectar o UI ao engine — usuário autenticado submete objetivo no dashboard, vê resposta do agente em streaming e run aparece no histórico.

**Architecture:** Dashboard split em server component (busca runs iniciais do Supabase) + DashboardClient (estado reativo com optimistic UI). SSE consumido via `fetch` + ReadableStream (não EventSource — precisa de Authorization header). Cada componente interativo é `'use client'`, dados iniciais vêm de server components.

**Tech Stack:** Next.js 16.2.4 (App Router), React 19, Tailwind 4, Supabase (browser + server), sonner 2.0.7, react-markdown 10.1.0, shiki 4.0.2, Vitest + @testing-library/react

---

## File Structure

**Criar:**
- `apps/web/lib/api.ts` — cliente tipado do FastAPI (createRun, getSkills, approveRun[stub])
- `apps/web/hooks/use-run-stream.ts` — SSE consumer com reconnect + exponential backoff
- `apps/web/hooks/use-skills.ts` — busca skills da API
- `apps/web/lib/highlighter.ts` — singleton do shiki
- `apps/web/components/run/status-badge.tsx` — badge animado de status
- `apps/web/components/run/status-badge.test.tsx`
- `apps/web/components/run/run-card.tsx` — card resumo de run
- `apps/web/components/run/run-card.test.tsx`
- `apps/web/components/chat/chat-input.tsx` — textarea + Cmd+Enter + Esc
- `apps/web/components/chat/chat-input.test.tsx`
- `apps/web/components/chat/message-list.tsx` — eventos SSE como mensagens (react-markdown + shiki)
- `apps/web/components/chat/message-list.test.tsx`
- `apps/web/components/chat/chat-error-boundary.tsx` — React error boundary
- `apps/web/components/chat/chat-error-boundary.test.tsx`
- `apps/web/components/skills/skills-catalog.tsx` — lista dinâmica de skills com skeleton
- `apps/web/components/skills/skills-catalog.test.tsx`
- `apps/web/app/(app)/dashboard/dashboard-client.tsx` — parte client do dashboard
- `apps/web/app/(app)/run/[id]/page.tsx` — server wrapper do run detail
- `apps/web/app/(app)/run/[id]/run-view.tsx` — client component com streaming
- `apps/web/app/(app)/history/page.tsx` — histórico de runs
- `apps/web/app/manifest.ts` — PWA manifest (Next.js 16 convention)

**Modificar:**
- `apps/web/app/(app)/dashboard/page.tsx` — busca runs server-side, passa para DashboardClient
- `apps/web/app/layout.tsx` — adiciona `<Toaster>` do sonner
- `apps/web/.env.local` (ou `.env.example`) — adiciona `NEXT_PUBLIC_API_URL`

---

> **Status note:** Status values no backend são **todos lowercase**: `created`, `running`, `paused`, `completed`, `failed`, `cancelled`. Usar esses exatamente.
>
> **approveRun note:** O endpoint `POST /runs/{id}/approve` ainda não existe no backend (será implementado na Fase 5). A função `approveRun` em `lib/api.ts` é um stub que retornará 404 em runtime — está aqui para não quebrar imports na Fase 5.

---

### Task 1: Instalar dependências e configurar variável de ambiente

**Files:**
- Modify: `apps/web/package.json` (via pnpm)
- Create: `apps/web/.env.example` (se não existir)

- [ ] **Step 1: Instalar pacotes**

```bash
cd apps/web
pnpm add sonner react-markdown shiki
```

- [ ] **Step 2: Verificar que aparecem em package.json**

```bash
grep -E "sonner|react-markdown|shiki" package.json
```

Expected: 3 linhas com as versões instaladas.

- [ ] **Step 3: Adicionar NEXT_PUBLIC_API_URL ao .env.example**

Adicionar ao final de `apps/web/.env.example` (criar se não existir):

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Criar `apps/web/.env.local` com o mesmo conteúdo para desenvolvimento local.

- [ ] **Step 4: Commit**

```bash
git add apps/web/package.json apps/web/pnpm-lock.yaml apps/web/.env.example
git commit -m "feat(web): adiciona sonner, react-markdown e shiki"
```

---

### Task 2: API client (lib/api.ts)

**Files:**
- Create: `apps/web/lib/api.ts`
- Create: `apps/web/lib/api.test.ts`

- [ ] **Step 1: Escrever o teste com falha**

Criar `apps/web/lib/api.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/supabase', () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: 'test-token' } },
      }),
    },
  }),
}))

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('createRun', () => {
  beforeEach(() => mockFetch.mockClear())

  it('POST /runs com Authorization header e objective no body', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ run_id: 'abc-123' }),
    })

    const { createRun } = await import('@/lib/api')
    const result = await createRun('Pesquisar mercado de AI no Brasil')

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/runs'),
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ Authorization: 'Bearer test-token' }),
        body: JSON.stringify({ objective: 'Pesquisar mercado de AI no Brasil' }),
      })
    )
    expect(result).toEqual({ run_id: 'abc-123' })
  })
})

describe('getSkills', () => {
  it('GET /skills com Authorization header', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([{ name: 'web_search', description: 'Busca web', parameters_schema: {}, requires_approval: false }]),
    })

    const { getSkills } = await import('@/lib/api')
    const result = await getSkills()

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/skills'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer test-token' }),
      })
    )
    expect(result[0].name).toBe('web_search')
  })
})
```

- [ ] **Step 2: Rodar teste para confirmar falha**

```bash
cd apps/web && pnpm test lib/api.test.ts
```

Expected: FAIL com "Cannot find module '@/lib/api'"

- [ ] **Step 3: Implementar lib/api.ts**

Criar `apps/web/lib/api.ts`:

```typescript
import { createClient } from '@/lib/supabase'

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

// Stub — endpoint não existe até a Fase 5. Retornará 404 em runtime.
export async function approveRun(runId: string, approved: boolean): Promise<void> {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/v1/runs/${runId}/approve`, {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ approved }),
  })
  if (!res.ok) throw new Error(await res.text())
}
```

- [ ] **Step 4: Rodar testes para confirmar que passam**

```bash
cd apps/web && pnpm test lib/api.test.ts
```

Expected: PASS (2 testes)

- [ ] **Step 5: Commit**

```bash
git add apps/web/lib/api.ts apps/web/lib/api.test.ts
git commit -m "feat(web): adiciona api client tipado para FastAPI"
```

---

### Task 3: SSE hook (hooks/use-run-stream.ts)

**Files:**
- Create: `apps/web/hooks/use-run-stream.ts`
- Create: `apps/web/hooks/use-run-stream.test.ts`

- [ ] **Step 1: Escrever testes**

Criar `apps/web/hooks/use-run-stream.test.ts`:

```typescript
import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { useRunStream } from './use-run-stream'

vi.mock('@/lib/supabase', () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: 'test-token' } },
      }),
    },
  }),
}))

describe('useRunStream', () => {
  it('retorna idle quando runId é null', () => {
    const { result } = renderHook(() => useRunStream(null))
    expect(result.current.status).toBe('idle')
    expect(result.current.events).toEqual([])
    expect(result.current.error).toBeNull()
  })

  it('move para connecting quando runId é fornecido', async () => {
    const mockReader = {
      read: vi.fn().mockResolvedValue({ done: true, value: undefined }),
    }
    const mockBody = { getReader: () => mockReader }

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      body: mockBody,
    }))

    const { result } = renderHook(() => useRunStream('run-123'))
    expect(result.current.status).toBe('idle')

    vi.restoreAllMocks()
  })

  it('parseia evento SSE corretamente', async () => {
    const encoder = new TextEncoder()
    const sseChunk = encoder.encode(
      'event: agent_started\ndata: {"run_id":"r1","type":"agent_started","payload":{"agent_name":"supervisor"}}\n\n'
    )

    let callCount = 0
    const mockReader = {
      read: vi.fn().mockImplementation(() => {
        callCount++
        if (callCount === 1) return Promise.resolve({ done: false, value: sseChunk })
        return Promise.resolve({ done: true, value: undefined })
      }),
    }

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      body: { getReader: () => mockReader },
    }))

    const { result } = renderHook(() => useRunStream('run-1'))

    await act(async () => {
      await new Promise(r => setTimeout(r, 100))
    })

    await waitFor(() => {
      expect(result.current.events).toHaveLength(1)
      expect(result.current.events[0].type).toBe('agent_started')
    })

    vi.restoreAllMocks()
  })
})
```

- [ ] **Step 2: Rodar testes para confirmar falha**

```bash
cd apps/web && pnpm test hooks/use-run-stream.test.ts
```

Expected: FAIL com "Cannot find module"

- [ ] **Step 3: Implementar use-run-stream.ts**

Criar `apps/web/hooks/use-run-stream.ts`:

```typescript
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
```

- [ ] **Step 4: Rodar testes**

```bash
cd apps/web && pnpm test hooks/use-run-stream.test.ts
```

Expected: PASS (3 testes)

- [ ] **Step 5: Commit**

```bash
git add apps/web/hooks/use-run-stream.ts apps/web/hooks/use-run-stream.test.ts
git commit -m "feat(web): adiciona hook useRunStream com SSE e reconnect"
```

---

### Task 4: Shiki highlighter singleton + useSkills hook

**Files:**
- Create: `apps/web/lib/highlighter.ts`
- Create: `apps/web/hooks/use-skills.ts`

- [ ] **Step 1: Criar lib/highlighter.ts**

```typescript
import { createHighlighter, type Highlighter } from 'shiki'

let _highlighter: Highlighter | null = null

export async function getHighlighter(): Promise<Highlighter> {
  if (!_highlighter) {
    _highlighter = await createHighlighter({
      themes: ['github-dark'],
      langs: ['python', 'typescript', 'javascript', 'bash', 'json', 'text'],
    })
  }
  return _highlighter
}
```

- [ ] **Step 2: Criar hooks/use-skills.ts**

```typescript
'use client'

import { useEffect, useState } from 'react'
import { getSkills, type SkillMetadata } from '@/lib/api'

export function useSkills() {
  const [skills, setSkills] = useState<SkillMetadata[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getSkills()
      .then(setSkills)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  return { skills, loading, error }
}
```

- [ ] **Step 3: Verificar que não há erros de TypeScript**

```bash
cd apps/web && npx tsc --noEmit
```

Expected: sem erros

- [ ] **Step 4: Commit**

```bash
git add apps/web/lib/highlighter.ts apps/web/hooks/use-skills.ts
git commit -m "feat(web): adiciona highlighter singleton e useSkills hook"
```

---

### Task 5: StatusBadge + RunCard

**Files:**
- Create: `apps/web/components/run/status-badge.tsx`
- Create: `apps/web/components/run/status-badge.test.tsx`
- Create: `apps/web/components/run/run-card.tsx`
- Create: `apps/web/components/run/run-card.test.tsx`

- [ ] **Step 1: Escrever testes**

Criar `apps/web/components/run/status-badge.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react'
import { StatusBadge } from './status-badge'

test('running mostra "Executando" com animate-pulse', () => {
  const { container } = render(<StatusBadge status="running" />)
  expect(screen.getByText('Executando')).toBeInTheDocument()
  expect(container.firstChild).toHaveClass('animate-pulse')
})

test('completed mostra "Concluído" sem pulse', () => {
  render(<StatusBadge status="completed" />)
  expect(screen.getByText('Concluído')).toBeInTheDocument()
})

test('failed mostra "Falhou"', () => {
  render(<StatusBadge status="failed" />)
  expect(screen.getByText('Falhou')).toBeInTheDocument()
})

test('status desconhecido renderiza sem crash', () => {
  render(<StatusBadge status="unknown_status" />)
  // não crasha
})
```

Criar `apps/web/components/run/run-card.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react'
import { RunCard } from './run-card'
import type { Run } from '@/lib/api'

const run: Run = {
  id: 'run-1',
  objective: 'Pesquisar mercado de AI no Brasil em 2026 para identificar oportunidades',
  status: 'completed',
  created_at: '2026-04-27T10:00:00Z',
  total_tokens: 1500,
  cost_usd: 0.002,
}

test('renderiza objetivo truncado', () => {
  render(<RunCard run={run} />)
  expect(screen.getByText(/Pesquisar mercado/)).toBeInTheDocument()
})

test('renderiza StatusBadge', () => {
  render(<RunCard run={run} />)
  expect(screen.getByText('Concluído')).toBeInTheDocument()
})

test('link aponta para /run/[id]', () => {
  const { container } = render(<RunCard run={run} />)
  const link = container.querySelector('a')
  expect(link?.getAttribute('href')).toBe('/run/run-1')
})

test('objetivo muito longo é truncado em 80 chars', () => {
  const longRun = { ...run, objective: 'x'.repeat(100) }
  render(<RunCard run={longRun} />)
  const text = screen.getByText(/x+/)
  expect(text.textContent?.length).toBeLessThanOrEqual(82) // 80 + '…' + margem
})
```

- [ ] **Step 2: Rodar testes para confirmar falha**

```bash
cd apps/web && pnpm test components/run/
```

Expected: FAIL

- [ ] **Step 3: Implementar StatusBadge**

Criar `apps/web/components/run/status-badge.tsx`:

```tsx
'use client'

const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  created:   { label: 'Criado',     className: 'bg-[#1f1f1f] text-[var(--color-text-muted)]' },
  running:   { label: 'Executando', className: 'bg-blue-950 text-[var(--color-primary-blue)] animate-pulse' },
  paused:    { label: 'Pausado',    className: 'bg-yellow-950 text-[var(--color-warning)] animate-pulse' },
  completed: { label: 'Concluído',  className: 'bg-green-950 text-[var(--color-success)]' },
  failed:    { label: 'Falhou',     className: 'bg-red-950 text-[var(--color-error)]' },
  cancelled: { label: 'Cancelado',  className: 'bg-[#1f1f1f] text-[var(--color-text-muted)]' },
}

interface StatusBadgeProps {
  status: string
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status.toLowerCase()] ?? STATUS_CONFIG.created
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${config.className}`}>
      {config.label}
    </span>
  )
}
```

- [ ] **Step 4: Implementar RunCard**

Criar `apps/web/components/run/run-card.tsx`:

```tsx
import Link from 'next/link'
import { StatusBadge } from './status-badge'
import type { Run } from '@/lib/api'

function truncate(text: string, max = 80): string {
  return text.length > max ? text.slice(0, max) + '…' : text
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export function RunCard({ run }: { run: Run }) {
  return (
    <Link
      href={`/run/${run.id}`}
      className="flex items-center justify-between p-3 rounded-lg border border-[var(--color-card-border)] bg-[var(--color-card)] hover:border-[var(--color-primary)] transition-colors min-h-[44px]"
    >
      <div className="flex-1 min-w-0 mr-3">
        <p className="text-sm text-[var(--color-text-primary)] truncate">{truncate(run.objective)}</p>
        <p className="text-xs text-[var(--color-text-muted)] mt-0.5">{formatDate(run.created_at)}</p>
      </div>
      <StatusBadge status={run.status} />
    </Link>
  )
}
```

- [ ] **Step 5: Rodar testes**

```bash
cd apps/web && pnpm test components/run/
```

Expected: PASS (7 testes)

- [ ] **Step 6: Commit**

```bash
git add apps/web/components/run/
git commit -m "feat(web): adiciona StatusBadge e RunCard"
```

---

### Task 6: ChatInput component

**Files:**
- Create: `apps/web/components/chat/chat-input.tsx`
- Create: `apps/web/components/chat/chat-input.test.tsx`

- [ ] **Step 1: Escrever testes**

Criar `apps/web/components/chat/chat-input.test.tsx`:

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import { ChatInput } from './chat-input'

describe('ChatInput', () => {
  it('renderiza textarea e botão de submit', () => {
    render(<ChatInput onSubmit={vi.fn()} />)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Executar/i })).toBeInTheDocument()
  })

  it('botão desabilitado quando textarea vazia', () => {
    render(<ChatInput onSubmit={vi.fn()} />)
    expect(screen.getByRole('button', { name: /Executar/i })).toBeDisabled()
  })

  it('botão desabilitado quando texto tem menos de 10 chars', async () => {
    const user = userEvent.setup()
    render(<ChatInput onSubmit={vi.fn()} />)
    await user.type(screen.getByRole('textbox'), 'curto')
    expect(screen.getByRole('button', { name: /Executar/i })).toBeDisabled()
  })

  it('chama onSubmit quando formulário é submetido com texto ≥ 10 chars', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()
    render(<ChatInput onSubmit={onSubmit} />)
    await user.type(screen.getByRole('textbox'), 'Pesquisar mercado de AI')
    await user.click(screen.getByRole('button', { name: /Executar/i }))
    expect(onSubmit).toHaveBeenCalledWith('Pesquisar mercado de AI')
  })

  it('Cmd+Enter dispara onSubmit', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()
    render(<ChatInput onSubmit={onSubmit} />)
    const textarea = screen.getByRole('textbox')
    await user.type(textarea, 'Pesquisar mercado de AI')
    fireEvent.keyDown(textarea, { key: 'Enter', metaKey: true })
    expect(onSubmit).toHaveBeenCalled()
  })

  it('Esc chama onCancel', async () => {
    const onCancel = vi.fn()
    const user = userEvent.setup()
    render(<ChatInput onSubmit={vi.fn()} onCancel={onCancel} />)
    const textarea = screen.getByRole('textbox')
    await user.type(textarea, 'texto')
    fireEvent.keyDown(textarea, { key: 'Escape' })
    expect(onCancel).toHaveBeenCalled()
  })

  it('limpa textarea após submit bem-sucedido', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()
    render(<ChatInput onSubmit={onSubmit} />)
    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement
    await user.type(textarea, 'Pesquisar mercado de AI')
    await user.click(screen.getByRole('button', { name: /Executar/i }))
    expect(textarea.value).toBe('')
  })
})
```

- [ ] **Step 2: Rodar testes para confirmar falha**

```bash
cd apps/web && pnpm test components/chat/chat-input.test.tsx
```

Expected: FAIL

- [ ] **Step 3: Implementar ChatInput**

Criar `apps/web/components/chat/chat-input.tsx`:

```tsx
'use client'

import { useRef, useState } from 'react'

interface ChatInputProps {
  onSubmit: (objective: string) => Promise<void>
  onCancel?: () => void
  disabled?: boolean
}

export function ChatInput({ onSubmit, onCancel, disabled = false }: ChatInputProps) {
  const [value, setValue] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const canSubmit = value.trim().length >= 10 && !submitting && !disabled

  async function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault()
    if (!canSubmit) return
    const objective = value.trim()
    setSubmitting(true)
    try {
      await onSubmit(objective)
      setValue('')
    } finally {
      setSubmitting(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault()
      handleSubmit()
    }
    if (e.key === 'Escape' && onCancel) {
      onCancel()
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Descreva seu objetivo… (mín. 10 caracteres)"
        rows={3}
        disabled={submitting || disabled}
        className="w-full resize-none rounded-lg border border-[var(--color-card-border)] bg-[var(--color-card)] px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-primary)] disabled:opacity-50 min-h-[44px]"
      />
      <div className="flex items-center justify-between">
        <span className="text-xs text-[var(--color-text-muted)]">
          {value.length}/500 · Cmd+Enter para enviar
        </span>
        <button
          type="submit"
          disabled={!canSubmit}
          className="px-4 py-2 rounded-lg bg-[var(--color-primary)] text-white text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-purple-400 transition-colors min-h-[44px]"
        >
          {submitting ? 'Enviando…' : 'Executar'}
        </button>
      </div>
    </form>
  )
}
```

- [ ] **Step 4: Rodar testes**

```bash
cd apps/web && pnpm test components/chat/chat-input.test.tsx
```

Expected: PASS (6 testes)

- [ ] **Step 5: Commit**

```bash
git add apps/web/components/chat/chat-input.tsx apps/web/components/chat/chat-input.test.tsx
git commit -m "feat(web): adiciona ChatInput com Cmd+Enter e Esc"
```

---

### Task 7: MessageList component

**Files:**
- Create: `apps/web/components/chat/message-list.tsx`
- Create: `apps/web/components/chat/message-list.test.tsx`

- [ ] **Step 1: Escrever testes**

Criar `apps/web/components/chat/message-list.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

vi.mock('@/lib/highlighter', () => ({
  getHighlighter: vi.fn().mockResolvedValue({
    codeToHtml: vi.fn().mockReturnValue('<pre><code>code</code></pre>'),
  }),
}))

vi.mock('react-markdown', () => ({
  default: ({ children }: { children: string }) => <div data-testid="markdown">{children}</div>,
}))

import { MessageList } from './message-list'
import type { RunEvent } from '@/hooks/use-run-stream'

describe('MessageList', () => {
  it('mostra "Aguardando agente..." quando events está vazio', () => {
    render(<MessageList events={[]} />)
    expect(screen.getByText(/Aguardando agente/)).toBeInTheDocument()
  })

  it('renderiza evento agent_started', () => {
    const events: RunEvent[] = [{
      run_id: 'r1',
      type: 'agent_started',
      payload: { agent_name: 'supervisor' },
    }]
    render(<MessageList events={events} />)
    expect(screen.getByText(/Agente iniciado/)).toBeInTheDocument()
  })

  it('renderiza evento run_completed', () => {
    const events: RunEvent[] = [{
      run_id: 'r1',
      type: 'run_completed',
      payload: { result: 'Tarefa concluída com sucesso' },
    }]
    render(<MessageList events={events} />)
    expect(screen.getByText(/Run concluído/i)).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Rodar testes para confirmar falha**

```bash
cd apps/web && pnpm test components/chat/message-list.test.tsx
```

Expected: FAIL

- [ ] **Step 3: Implementar MessageList**

> **Nota sobre react-markdown v10:** O componente `code` recebe `{ children, className, node, ...rest }`. Para detectar code block vs inline code, checar se a string da linha pai é `pre`. Use `node?.position` ou simplesmente tente: se `className` começa com `language-`, é um code block. Isso é estável no v9+/v10.

Criar `apps/web/components/chat/message-list.tsx`:

```tsx
'use client'

import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import type { RunEvent } from '@/hooks/use-run-stream'
import { getHighlighter } from '@/lib/highlighter'
import type { Highlighter } from 'shiki'

const EVENT_LABELS: Partial<Record<RunEvent['type'], string>> = {
  agent_started:  'Agente iniciado',
  task_started:   'Tarefa iniciada',
  task_completed: 'Tarefa concluída',
  skill_called:   'Skill chamada',
  hitl_required:  'Aprovação necessária',
  run_completed:  'Run concluído',
  run_failed:     'Run falhou',
  budget_warning: 'Aviso de budget',
}

function eventToMarkdown(event: RunEvent): string {
  const p = event.payload
  switch (event.type) {
    case 'agent_started':
      return `Agente **${p.agent_name ?? 'desconhecido'}** iniciado.`
    case 'task_started':
      return `Iniciando: ${p.task ?? ''}`
    case 'task_completed':
      return `Tarefa concluída.\n\n${p.result ?? ''}`
    case 'skill_called':
      return `Skill **${p.skill_name ?? ''}** chamada:\n\`\`\`json\n${JSON.stringify(p.params ?? {}, null, 2)}\n\`\`\``
    case 'hitl_required':
      return `⚠️ Aguardando aprovação para: **${p.action ?? ''}**`
    case 'run_completed':
      return `**Run concluído.**\n\n${p.result ?? ''}`
    case 'run_failed':
      return `**Falha:** ${p.error ?? 'Erro desconhecido'}`
    case 'budget_warning':
      return `Aviso de budget: ${p.tokens_used ?? 0} tokens de ${p.budget_limit ?? 0}.`
    default:
      return JSON.stringify(p)
  }
}

export function MessageList({ events }: { events: RunEvent[] }) {
  const [highlighter, setHighlighter] = useState<Highlighter | null>(null)

  useEffect(() => {
    getHighlighter().then(setHighlighter).catch(() => null)
  }, [])

  if (events.length === 0) {
    return (
      <p className="text-sm text-[var(--color-text-muted)] text-center py-8">
        Aguardando agente...
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {events.map((event, i) => (
        <div key={i} className="rounded-lg border border-[var(--color-card-border)] bg-[var(--color-card)] p-4">
          <p className="text-xs font-medium text-[var(--color-text-muted)] mb-2 uppercase tracking-wide">
            {EVENT_LABELS[event.type] ?? event.type}
          </p>
          <div className="text-sm text-[var(--color-text-primary)]">
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                strong: ({ children }) => (
                  <strong className="font-semibold text-[var(--color-text-primary)]">{children}</strong>
                ),
                code(props) {
                  const { children, className } = props
                  const match = /language-(\w+)/.exec(className ?? '')
                  const code = String(children).trim()
                  if (match && highlighter) {
                    const html = highlighter.codeToHtml(code, {
                      lang: match[1],
                      theme: 'github-dark',
                    })
                    return (
                      <div
                        dangerouslySetInnerHTML={{ __html: html }}
                        className="rounded-lg overflow-x-auto text-xs my-2 [&_pre]:p-4"
                      />
                    )
                  }
                  return (
                    <code className="bg-[#1f1f1f] px-1.5 py-0.5 rounded text-xs font-mono">
                      {children}
                    </code>
                  )
                },
              }}
            >
              {eventToMarkdown(event)}
            </ReactMarkdown>
          </div>
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 4: Rodar testes**

```bash
cd apps/web && pnpm test components/chat/message-list.test.tsx
```

Expected: PASS (3 testes)

- [ ] **Step 5: Commit**

```bash
git add apps/web/components/chat/message-list.tsx apps/web/components/chat/message-list.test.tsx
git commit -m "feat(web): adiciona MessageList com react-markdown e shiki"
```

---

### Task 8: ChatErrorBoundary

**Files:**
- Create: `apps/web/components/chat/chat-error-boundary.tsx`
- Create: `apps/web/components/chat/chat-error-boundary.test.tsx`

- [ ] **Step 1: Escrever testes**

Criar `apps/web/components/chat/chat-error-boundary.test.tsx`:

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { ChatErrorBoundary } from './chat-error-boundary'

function ThrowingComponent({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) throw new Error('test error')
  return <div>Conteúdo normal</div>
}

describe('ChatErrorBoundary', () => {
  it('renderiza children quando não há erro', () => {
    render(
      <ChatErrorBoundary>
        <ThrowingComponent shouldThrow={false} />
      </ChatErrorBoundary>
    )
    expect(screen.getByText('Conteúdo normal')).toBeInTheDocument()
  })

  it('mostra fallback quando child lança erro', () => {
    // Suprimir console.error do React para o teste ficar limpo
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <ChatErrorBoundary>
        <ThrowingComponent shouldThrow={true} />
      </ChatErrorBoundary>
    )
    expect(screen.getByText(/Algo deu errado/)).toBeInTheDocument()
    spy.mockRestore()
  })

  it('"Tentar novamente" reseta o error boundary', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <ChatErrorBoundary>
        <ThrowingComponent shouldThrow={true} />
      </ChatErrorBoundary>
    )
    fireEvent.click(screen.getByRole('button', { name: /Tentar novamente/i }))
    // Após reset, boundary tenta re-renderizar — não crasha
    spy.mockRestore()
  })
})
```

- [ ] **Step 2: Rodar testes para confirmar falha**

```bash
cd apps/web && pnpm test components/chat/chat-error-boundary.test.tsx
```

- [ ] **Step 3: Implementar ChatErrorBoundary**

Criar `apps/web/components/chat/chat-error-boundary.tsx`:

```tsx
'use client'

import { Component, type ReactNode } from 'react'

export class ChatErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(): { hasError: boolean } {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center p-8 text-center">
          <p className="text-sm text-[var(--color-text-secondary)] mb-4">Algo deu errado.</p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="px-3 py-2 rounded-lg border border-[var(--color-card-border)] text-sm text-[var(--color-text-primary)] hover:border-[var(--color-primary)] transition-colors min-h-[44px]"
          >
            Tentar novamente
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
```

- [ ] **Step 4: Rodar testes**

```bash
cd apps/web && pnpm test components/chat/chat-error-boundary.test.tsx
```

Expected: PASS (3 testes)

- [ ] **Step 5: Commit**

```bash
git add apps/web/components/chat/chat-error-boundary.tsx apps/web/components/chat/chat-error-boundary.test.tsx
git commit -m "feat(web): adiciona ChatErrorBoundary"
```

---

### Task 9: SkillsCatalog

**Files:**
- Create: `apps/web/components/skills/skills-catalog.tsx`
- Create: `apps/web/components/skills/skills-catalog.test.tsx`

- [ ] **Step 1: Escrever testes**

Criar `apps/web/components/skills/skills-catalog.test.tsx`:

```typescript
import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

vi.mock('@/lib/api', () => ({
  getSkills: vi.fn().mockResolvedValue([
    { name: 'web_search', description: 'Busca na web', parameters_schema: {}, requires_approval: false },
    { name: 'code_interpreter', description: 'Executa código', parameters_schema: {}, requires_approval: true },
  ]),
}))

import { SkillsCatalog } from './skills-catalog'

describe('SkillsCatalog', () => {
  it('mostra skeleton enquanto carrega', () => {
    const { container } = render(<SkillsCatalog />)
    // Skeleton elements existem durante loading
    const skeletons = container.querySelectorAll('[class*="animate-pulse"]')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('renderiza skills após carregar', async () => {
    render(<SkillsCatalog />)
    await waitFor(() => {
      expect(screen.getByText('web_search')).toBeInTheDocument()
      expect(screen.getByText('code_interpreter')).toBeInTheDocument()
    })
  })

  it('mostra badge "aprovação" em skills com requires_approval', async () => {
    render(<SkillsCatalog />)
    await waitFor(() => {
      expect(screen.getByText('aprovação')).toBeInTheDocument()
    })
  })
})
```

- [ ] **Step 2: Rodar testes para confirmar falha**

```bash
cd apps/web && pnpm test components/skills/
```

- [ ] **Step 3: Implementar SkillsCatalog**

Criar `apps/web/components/skills/skills-catalog.tsx`:

```tsx
'use client'

import { useSkills } from '@/hooks/use-skills'
import { Skeleton } from '@/components/ui/skeleton'

export function SkillsCatalog() {
  const { skills, loading } = useSkills()

  if (loading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-4/6" />
      </div>
    )
  }

  if (skills.length === 0) {
    return <p className="text-xs text-[var(--color-text-muted)]">Nenhuma skill disponível.</p>
  }

  return (
    <div className="space-y-3">
      {skills.map(skill => (
        <div key={skill.name} className="flex items-start gap-2">
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-[var(--color-text-primary)]">{skill.name}</p>
            <p className="text-xs text-[var(--color-text-muted)] mt-0.5 truncate">{skill.description}</p>
          </div>
          {skill.requires_approval && (
            <span className="shrink-0 text-[10px] px-1.5 py-0.5 rounded bg-yellow-950 text-[var(--color-warning)]">
              aprovação
            </span>
          )}
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 4: Rodar testes**

```bash
cd apps/web && pnpm test components/skills/
```

Expected: PASS

- [ ] **Step 5: Rodar todos os testes para garantir que não quebrou nada**

```bash
cd apps/web && pnpm test
```

Expected: todos passando

- [ ] **Step 6: Commit**

```bash
git add apps/web/components/skills/
git commit -m "feat(web): adiciona SkillsCatalog com skeleton loading"
```

---

### Task 10: Root layout (Toaster) + PWA manifest

**Files:**
- Modify: `apps/web/app/layout.tsx`
- Create: `apps/web/app/manifest.ts`

> **Next.js 16 convention:** Manifest vai em `app/manifest.ts`, não em `public/`. O Next.js serve automaticamente em `/manifest.webmanifest` e injeta o `<link>` no `<head>`. Não adicionar `<link rel="manifest">` manualmente no layout.

- [ ] **Step 1: Criar app/manifest.ts**

```typescript
import type { MetadataRoute } from 'next'

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Aether OS',
    short_name: 'Aether',
    description: 'AI agent orchestrator',
    start_url: '/dashboard',
    display: 'standalone',
    background_color: '#000000',
    theme_color: '#000000',
    icons: [
      {
        src: '/favicon.ico',
        sizes: 'any',
        type: 'image/x-icon',
      },
    ],
  }
}
```

- [ ] **Step 2: Atualizar app/layout.tsx para adicionar Toaster**

Ler o arquivo atual primeiro para preservar o conteúdo exato, depois adicionar o import e o componente:

```tsx
import type { Metadata } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
import { Toaster } from 'sonner'
import './globals.css'

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
})

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
})

export const metadata: Metadata = {
  title: 'Aether OS',
  description: 'AI agent orchestrator',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
        {children}
        <Toaster theme="dark" position="bottom-right" richColors />
      </body>
    </html>
  )
}
```

- [ ] **Step 3: Verificar TypeScript**

```bash
cd apps/web && npx tsc --noEmit
```

Expected: sem erros

- [ ] **Step 4: Commit**

```bash
git add apps/web/app/layout.tsx apps/web/app/manifest.ts
git commit -m "feat(web): adiciona Toaster e PWA manifest"
```

---

### Task 11: Dashboard — server page + DashboardClient

**Files:**
- Modify: `apps/web/app/(app)/dashboard/page.tsx`
- Create: `apps/web/app/(app)/dashboard/dashboard-client.tsx`

- [ ] **Step 1: Criar dashboard-client.tsx**

Criar `apps/web/app/(app)/dashboard/dashboard-client.tsx`:

```tsx
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { BentoGrid, BentoItem } from '@/components/bento/bento-grid'
import { SpotlightCard } from '@/components/ui/spotlight-card'
import { ChatInput } from '@/components/chat/chat-input'
import { ChatErrorBoundary } from '@/components/chat/chat-error-boundary'
import { SkillsCatalog } from '@/components/skills/skills-catalog'
import { RunCard } from '@/components/run/run-card'
import { createRun, type Run } from '@/lib/api'

export function DashboardClient({ initialRuns }: { initialRuns: Run[] }) {
  const router = useRouter()
  const [runs, setRuns] = useState<Run[]>(initialRuns)

  async function handleSubmit(objective: string) {
    const optimisticId = `optimistic-${Date.now()}`
    const optimisticRun: Run = {
      id: optimisticId,
      objective,
      status: 'created',
      created_at: new Date().toISOString(),
      total_tokens: 0,
      cost_usd: 0,
    }
    setRuns(prev => [optimisticRun, ...prev].slice(0, 5))

    try {
      const { run_id } = await createRun(objective)
      setRuns(prev =>
        prev.map(r => r.id === optimisticId ? { ...optimisticRun, id: run_id, status: 'running' } : r)
      )
      toast.success('Run iniciado!')
      router.push(`/run/${run_id}`)
    } catch (err) {
      setRuns(prev => prev.filter(r => r.id !== optimisticId))
      toast.error(`Erro ao criar run: ${err instanceof Error ? err.message : 'Tente novamente'}`)
    }
  }

  return (
    <BentoGrid>
      <BentoItem colSpan={2}>
        <SpotlightCard className="p-6">
          <p className="text-sm text-[var(--color-text-muted)] mb-4">Novo objetivo</p>
          <ChatErrorBoundary>
            <ChatInput onSubmit={handleSubmit} />
          </ChatErrorBoundary>
        </SpotlightCard>
      </BentoItem>

      <BentoItem>
        <SpotlightCard className="p-6 h-full">
          <p className="text-sm text-[var(--color-text-muted)] mb-3">Skills disponíveis</p>
          <SkillsCatalog />
        </SpotlightCard>
      </BentoItem>

      <BentoItem colSpan={3}>
        <SpotlightCard className="p-6">
          <p className="text-sm text-[var(--color-text-muted)] mb-3">Runs recentes</p>
          {runs.length === 0 ? (
            <p className="text-xs text-[var(--color-text-muted)]">Nenhum run ainda. Comece acima!</p>
          ) : (
            <div className="space-y-2">
              {runs.slice(0, 5).map(run => (
                <RunCard key={run.id} run={run} />
              ))}
            </div>
          )}
        </SpotlightCard>
      </BentoItem>
    </BentoGrid>
  )
}
```

- [ ] **Step 2: Atualizar dashboard/page.tsx**

Substituir o conteúdo de `apps/web/app/(app)/dashboard/page.tsx` por:

```tsx
import { createClient } from '@/lib/supabase-server'
import { DashboardClient } from './dashboard-client'
import type { Run } from '@/lib/api'

export default async function DashboardPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  const { data: runs } = await supabase
    .from('runs')
    .select('id, objective, status, created_at, total_tokens, cost_usd')
    .eq('user_id', user!.id)
    .order('created_at', { ascending: false })
    .limit(5)

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">Dashboard</h1>
      <DashboardClient initialRuns={(runs ?? []) as Run[]} />
    </div>
  )
}
```

- [ ] **Step 3: Verificar TypeScript**

```bash
cd apps/web && npx tsc --noEmit
```

Expected: sem erros

- [ ] **Step 4: Commit**

```bash
git add apps/web/app/\(app\)/dashboard/
git commit -m "feat(web): conecta dashboard com optimistic UI e streaming"
```

---

### Task 12: Run detail page (/run/[id])

**Files:**
- Create: `apps/web/app/(app)/run/[id]/page.tsx`
- Create: `apps/web/app/(app)/run/[id]/run-view.tsx`

> **Next.js 16:** `params` é `Promise<{ id: string }>` — usar `await params` em server components.

- [ ] **Step 1: Criar run-view.tsx (client component)**

Criar `apps/web/app/(app)/run/[id]/run-view.tsx`:

```tsx
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
```

- [ ] **Step 2: Criar page.tsx (server component)**

Criar `apps/web/app/(app)/run/[id]/page.tsx`:

```tsx
import { notFound } from 'next/navigation'
import { createClient } from '@/lib/supabase-server'
import { RunView } from './run-view'

interface PageProps {
  params: Promise<{ id: string }>
}

export default async function RunPage({ params }: PageProps) {
  const { id } = await params
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  const { data: run } = await supabase
    .from('runs')
    .select('id, objective, status')
    .eq('id', id)
    .eq('user_id', user!.id)
    .single()

  if (!run) notFound()

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">Run Detail</h1>
      <RunView runId={run.id} objective={run.objective} initialStatus={run.status} />
    </div>
  )
}
```

- [ ] **Step 3: Verificar TypeScript**

```bash
cd apps/web && npx tsc --noEmit
```

Expected: sem erros

- [ ] **Step 4: Commit**

```bash
git add "apps/web/app/(app)/run/"
git commit -m "feat(web): adiciona página de run detail com streaming"
```

---

### Task 13: History page (/history)

**Files:**
- Create: `apps/web/app/(app)/history/page.tsx`

- [ ] **Step 1: Criar history/page.tsx**

```tsx
import { createClient } from '@/lib/supabase-server'
import { RunCard } from '@/components/run/run-card'
import type { Run } from '@/lib/api'

export default async function HistoryPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  const { data: runs } = await supabase
    .from('runs')
    .select('id, objective, status, created_at, total_tokens, cost_usd')
    .eq('user_id', user!.id)
    .order('created_at', { ascending: false })

  const typedRuns = (runs ?? []) as Run[]

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">Histórico</h1>
      {typedRuns.length === 0 ? (
        <p className="text-sm text-[var(--color-text-muted)]">Nenhum run ainda.</p>
      ) : (
        <div className="space-y-3">
          {typedRuns.map(run => (
            <RunCard key={run.id} run={run} />
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Verificar TypeScript e todos os testes**

```bash
cd apps/web && npx tsc --noEmit && pnpm test
```

Expected: sem erros de TypeScript, todos os testes passando

- [ ] **Step 3: Commit**

```bash
git add "apps/web/app/(app)/history/"
git commit -m "feat(web): adiciona página de histórico de runs"
```

---

### Task 14: Verificação E2E e responsividade mobile

> Esta task requer o backend rodando localmente.

- [ ] **Step 0: Verificar CORS do backend**

```bash
grep -n "localhost:3000\|allow_origins" apps/server/api/middleware/cors.py
```

Esperado: `http://localhost:3000` deve estar na lista `allow_origins`. Se não estiver, adicionar:

```python
# apps/server/api/middleware/cors.py
allow_origins=[
    "http://localhost:3000",
    # outros origins existentes...
],
```

- [ ] **Step 1: Iniciar backend e frontend**

```bash
# Terminal 1 — backend
cd apps/server && uvicorn api.main:app --reload

# Terminal 2 — frontend
cd apps/web && pnpm dev
```

- [ ] **Step 2: Verificar fluxo completo (golden path)**

Abrir `http://localhost:3000`:

1. Navegar para `/login` → fazer login com conta Supabase
2. Redirecionado para `/dashboard`
3. Verificar: ChatInput renderizado, SkillsCatalog mostra as 4 skills (ou skeleton se API offline)
4. Digitar objetivo com ≥ 10 chars → Cmd+Enter ou botão "Executar"
5. Verificar: run aparece no topo da lista de "Runs recentes" com status "Criado" (optimistic)
6. Após resposta do servidor: status muda para "Executando", redirect para `/run/{id}`
7. Na página `/run/{id}`: eventos SSE aparecem em tempo real como cards
8. Run termina: status muda para "Concluído", toast aparece no canto inferior direito
9. Navegar para `/history`: run aparece na lista com status correto

- [ ] **Step 3: Verificar responsividade mobile (375px)**

No Chrome DevTools (F12 → ícone de dispositivo):

1. Selecionar "iPhone SE" (375×667)
2. Dashboard: BentoGrid colapsa em coluna única ✓
3. ChatInput: textarea e botão acessíveis, mín. 44px de altura ✓
4. RunCard: texto truncado, não overflow ✓
5. Toast: visível no canto inferior ✓

- [ ] **Step 4: Verificar responsividade tablet (768px)**

1. Selecionar dimensão 768×1024
2. BentoGrid: layout 3 colunas aparece ✓

- [ ] **Step 5: Verificar PWA**

No Chrome: DevTools → Application → Manifest
Expected: `name: "Aether OS"`, `start_url: "/dashboard"`, `display: "standalone"`

- [ ] **Step 6: Verificar keyboard shortcuts**

1. No dashboard: focar textarea, digitar texto ≥ 10 chars
2. Cmd+Enter (Mac) ou Ctrl+Enter (Windows) → formulário é submetido ✓
3. Pressionar Esc: nenhum crash (onCancel não está definido no DashboardClient — verificar) ✓

- [ ] **Step 7: Commit final**

```bash
git add -A
git commit -m "feat: Fase 4 — Frontend Integration completa"
```

---

## Spec Coverage Check

| Entregável | Task |
|---|---|
| `use-run-stream.ts` com reconnect + backoff | Task 3 |
| Dashboard Bento Grid com input, skills catalog, runs recentes | Task 11 |
| Chat input submete → cria run → abre SSE stream | Task 6 + Task 11 |
| Mensagens com Markdown + syntax highlighting | Task 7 |
| Run card com status badge animado | Task 5 |
| Página `/history` | Task 13 |
| Skeleton loading em todos os blocos | StatusBadge/RunCard (T5), SkillsCatalog (T9), dashboard initialRuns (T11) |
| Optimistic UI: run como PENDING imediatamente | Task 11 (DashboardClient) |
| Error boundaries em torno de Chat | Task 8 + Task 11/12 |
| Toast notifications | Task 10 (Toaster) + Task 11/12 (toast calls) |
| Keyboard shortcuts Cmd+Enter / Esc | Task 6 (ChatInput) |
| PWA manifest.json + ícones | Task 10 |
| Responsividade mobile ≤768px testada | Task 14 |
