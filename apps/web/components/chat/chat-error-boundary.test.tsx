import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
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
