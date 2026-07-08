import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { AdminView } from './admin-view'
import { getAdminRuns, getAdminUsers } from '@/lib/api'

vi.mock('@/lib/api', () => ({
  getAdminUsers: vi.fn(),
  getAdminRuns: vi.fn(),
}))

vi.mock('sonner', () => ({ toast: { error: vi.fn() } }))

describe('AdminView', () => {
  beforeEach(() => {
    vi.mocked(getAdminUsers).mockReset()
    vi.mocked(getAdminRuns).mockReset()
  })

  it('renderiza usuários e runs após carregar', async () => {
    vi.mocked(getAdminUsers).mockResolvedValue([
      { user_id: 'u1', email: 'a@test.com', role: 'admin', created_at: '2026-01-01T00:00:00Z', run_count: 3 },
    ])
    vi.mocked(getAdminRuns).mockResolvedValue([
      {
        id: 'r1', user_id: 'u1', user_email: 'a@test.com', objective: 'Testar sistema',
        status: 'COMPLETED', total_tokens: 100, cost_usd: 0.01, created_at: '2026-01-01T00:00:00Z',
      },
    ])

    render(<AdminView />)

    expect(await screen.findByText('Testar sistema')).toBeInTheDocument()
    expect(screen.getAllByText('a@test.com').length).toBeGreaterThan(0)
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('mostra estado vazio quando não há usuários nem runs', async () => {
    vi.mocked(getAdminUsers).mockResolvedValue([])
    vi.mocked(getAdminRuns).mockResolvedValue([])

    render(<AdminView />)

    expect(await screen.findByText('Nenhum usuário ainda.')).toBeInTheDocument()
    expect(screen.getByText('Nenhuma run ainda.')).toBeInTheDocument()
  })
})
