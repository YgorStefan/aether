import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ResetPasswordPage from './page'

const mockUpdateUser = vi.fn()
const mockPush = vi.fn()

vi.mock('@/lib/supabase', () => ({
  createClient: () => ({
    auth: { updateUser: mockUpdateUser },
  }),
}))

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}))

describe('ResetPasswordPage', () => {
  beforeEach(() => {
    mockUpdateUser.mockReset()
    mockPush.mockReset()
  })

  it('redefine a senha com sucesso', async () => {
    mockUpdateUser.mockResolvedValue({ error: null })
    const user = userEvent.setup()
    render(<ResetPasswordPage />)

    await user.type(screen.getByPlaceholderText('mínimo 6 caracteres'), 'novaSenha123')
    await user.click(screen.getByRole('button', { name: /Redefinir senha/i }))

    expect(mockUpdateUser).toHaveBeenCalledWith({ password: 'novaSenha123' })
    expect(await screen.findByText(/redefinida com sucesso/i)).toBeInTheDocument()
  })

  it('mostra erro quando o link expirou', async () => {
    mockUpdateUser.mockResolvedValue({ error: { message: '' } })
    const user = userEvent.setup()
    render(<ResetPasswordPage />)

    await user.type(screen.getByPlaceholderText('mínimo 6 caracteres'), 'novaSenha123')
    await user.click(screen.getByRole('button', { name: /Redefinir senha/i }))

    expect(await screen.findByText(/link pode ter expirado/i)).toBeInTheDocument()
  })
})
