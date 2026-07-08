// apps/web/components/run/budget-progress-bar.test.tsx
import { render, screen } from '@testing-library/react'
import { BudgetProgressBar } from './budget-progress-bar'

test('mostra tokens usados e limite formatados', () => {
  render(<BudgetProgressBar totalTokens={5000} budgetLimit={10000} costUsd={0.0015} />)
  expect(screen.getByText(/5\.000/)).toBeInTheDocument()
  expect(screen.getByText(/10\.000/)).toBeInTheDocument()
  expect(screen.getByText(/\$0\.0015/)).toBeInTheDocument()
})

test('barra roxa abaixo de 80%', () => {
  const { container } = render(
    <BudgetProgressBar totalTokens={5000} budgetLimit={10000} costUsd={0.001} />
  )
  const bar = container.querySelector('[data-testid="budget-bar"]')
  expect(bar?.className).toContain('bg-primary')
})

test('barra amarela entre 80% e 100%', () => {
  const { container } = render(
    <BudgetProgressBar totalTokens={8500} budgetLimit={10000} costUsd={0.002} />
  )
  const bar = container.querySelector('[data-testid="budget-bar"]')
  expect(bar?.className).toContain('bg-warning')
})

test('barra vermelha em 100%', () => {
  const { container } = render(
    <BudgetProgressBar totalTokens={10000} budgetLimit={10000} costUsd={0.003} />
  )
  const bar = container.querySelector('[data-testid="budget-bar"]')
  expect(bar?.className).toContain('bg-error')
})

test('budget zero não crasha', () => {
  const { container } = render(<BudgetProgressBar totalTokens={0} budgetLimit={0} costUsd={0} />)
  const bar = container.querySelector('[data-testid="budget-bar"]')
  expect(bar?.className).toContain('bg-primary')
})
