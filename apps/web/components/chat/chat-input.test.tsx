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
