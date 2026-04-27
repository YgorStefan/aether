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
