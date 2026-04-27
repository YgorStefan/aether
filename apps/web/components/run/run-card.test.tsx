import { render, screen } from '@testing-library/react'
import { RunCard } from './run-card'
import type { Run } from '@/lib/api'

vi.mock('next/link', () => ({
  default: ({ href, children, className }: { href: string; children: React.ReactNode; className?: string }) =>
    <a href={href} className={className}>{children}</a>
}))

const run: Run = {
  id: 'run-1',
  objective: 'Pesquisar mercado de AI no Brasil em 2026 para identificar oportunidades',
  status: 'completed',
  created_at: '2026-04-27T10:00:00Z',
  total_tokens: 1500,
  cost_usd: 0.002,
}

test('renderiza objetivo truncado', () => {
  render(<RunCard run={run} />)
  expect(screen.getByText(/Pesquisar mercado/)).toBeInTheDocument()
})

test('renderiza StatusBadge', () => {
  render(<RunCard run={run} />)
  expect(screen.getByText('Concluído')).toBeInTheDocument()
})

test('link aponta para /run/[id]', () => {
  const { container } = render(<RunCard run={run} />)
  const link = container.querySelector('a')
  expect(link?.getAttribute('href')).toBe('/run/run-1')
})

test('objetivo muito longo é truncado em 80 chars', () => {
  const longRun = { ...run, objective: 'x'.repeat(100) }
  render(<RunCard run={longRun} />)
  const text = screen.getByText(/x+/)
  expect(text.textContent?.length).toBeLessThanOrEqual(82) // 80 + '…' + margem
})
