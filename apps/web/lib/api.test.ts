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

describe('deleteAccount', () => {
  beforeEach(() => mockFetch.mockClear())

  it('DELETE /account com Authorization header', async () => {
    mockFetch.mockResolvedValue({ ok: true, text: () => Promise.resolve('') })

    const { deleteAccount } = await import('@/lib/api')
    await deleteAccount()

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/account'),
      expect.objectContaining({
        method: 'DELETE',
        headers: expect.objectContaining({ Authorization: 'Bearer test-token' }),
      })
    )
  })

  it('lança erro quando resposta não é ok', async () => {
    mockFetch.mockResolvedValue({ ok: false, text: () => Promise.resolve('erro interno') })

    const { deleteAccount } = await import('@/lib/api')
    await expect(deleteAccount()).rejects.toThrow('erro interno')
  })
})

describe('getMe', () => {
  it('GET /me retorna email e role', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ email: 'a@test.com', role: 'admin' }),
    })

    const { getMe } = await import('@/lib/api')
    const result = await getMe()

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/me'),
      expect.anything()
    )
    expect(result).toEqual({ email: 'a@test.com', role: 'admin' })
  })
})

describe('getAdminUsers e getAdminRuns', () => {
  it('GET /admin/users retorna lista de usuários', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve([]) })
    const { getAdminUsers } = await import('@/lib/api')
    await getAdminUsers()
    expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/api/v1/admin/users'), expect.anything())
  })

  it('GET /admin/runs retorna lista de runs', async () => {
    mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve([]) })
    const { getAdminRuns } = await import('@/lib/api')
    await getAdminRuns()
    expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining('/api/v1/admin/runs'), expect.anything())
  })
})
