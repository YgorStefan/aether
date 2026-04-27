import { renderHook, act, waitFor } from '@testing-library/react'
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
