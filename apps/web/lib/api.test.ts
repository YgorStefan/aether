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
