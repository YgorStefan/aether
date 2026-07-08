import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { HitlPanel } from './hitl-panel'
import { approveRun } from '@/lib/api'

vi.mock('@/lib/api', () => ({
  approveRun: vi.fn(),
}))

vi.mock('sonner', () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}))

describe('HitlPanel', () => {
  beforeEach(() => {
    vi.mocked(approveRun).mockReset()
  })

  it('mostra skill e parâmetros', () => {
    render(<HitlPanel runId="run-1" skill="web_search" params={{ query: 'AI' }} />)
    expect(screen.getByText('web_search')).toBeInTheDocument()
    expect(screen.getByText(/"query": "AI"/)).toBeInTheDocument()
  })

  it('reseta o loading após aprovação com sucesso', async () => {
    vi.mocked(approveRun).mockResolvedValue(undefined)
    const user = userEvent.setup()
    render(<HitlPanel runId="run-1" skill="web_search" params={{}} />)

    const approveButton = screen.getByRole('button', { name: /Aprovar/i })
    await user.click(approveButton)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Aprovar/i })).not.toBeDisabled()
    })
  })

  it('reseta o loading após falha', async () => {
    vi.mocked(approveRun).mockRejectedValue(new Error('network error'))
    const user = userEvent.setup()
    render(<HitlPanel runId="run-1" skill="web_search" params={{}} />)

    const rejectButton = screen.getByRole('button', { name: /Rejeitar/i })
    await user.click(rejectButton)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Rejeitar/i })).not.toBeDisabled()
    })
  })
})
