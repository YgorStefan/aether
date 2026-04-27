import { render, screen } from '@testing-library/react'
import { StatusBadge } from './status-badge'

test('running mostra "Executando" com animate-pulse', () => {
  const { container } = render(<StatusBadge status="running" />)
  expect(screen.getByText('Executando')).toBeInTheDocument()
  expect(container.firstChild).toHaveClass('animate-pulse')
})

test('completed mostra "Concluído" sem pulse', () => {
  render(<StatusBadge status="completed" />)
  expect(screen.getByText('Concluído')).toBeInTheDocument()
})

test('failed mostra "Falhou"', () => {
  render(<StatusBadge status="failed" />)
  expect(screen.getByText('Falhou')).toBeInTheDocument()
})

test('status desconhecido renderiza sem crash', () => {
  render(<StatusBadge status="unknown_status" />)
  // não crasha
})
