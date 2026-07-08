import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ForgotPasswordPage from './page'

const mockResetPasswordForEmail = vi.fn()

vi.mock('@/lib/supabase', () => ({
  createClient: () => ({
    auth: { resetPasswordForEmail: mockResetPasswordForEmail },
  }),
}))

describe('ForgotPasswordPage', () => {
  beforeEach(() => {
    mockResetPasswordForEmail.mockReset()
  })

  it('envia email de recuperação e mostra mensagem de sucesso', async () => {
    mockResetPasswordForEmail.mockResolvedValue({ error: null })
    const user = userEvent.setup()
    render(<ForgotPasswordPage />)

    await user.type(screen.getByPlaceholderText('seu@email.com'), 'user@test.com')
    await user.click(screen.getByRole('button', { name: /Enviar link/i }))

    expect(mockResetPasswordForEmail).toHaveBeenCalledWith(
      'user@test.com',
      expect.objectContaining({ redirectTo: expect.stringContaining('/reset-password') })
    )
    expect(await screen.findByText(/enviamos um link/i)).toBeInTheDocument()
  })

  it('mostra erro quando a requisição falha', async () => {
    mockResetPasswordForEmail.mockResolvedValue({ error: { message: 'Erro ao enviar' } })
    const user = userEvent.setup()
    render(<ForgotPasswordPage />)

    await user.type(screen.getByPlaceholderText('seu@email.com'), 'user@test.com')
    await user.click(screen.getByRole('button', { name: /Enviar link/i }))

    expect(await screen.findByText('Erro ao enviar')).toBeInTheDocument()
  })
})
