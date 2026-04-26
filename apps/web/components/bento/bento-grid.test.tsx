import { render, screen } from '@testing-library/react'
import { BentoGrid, BentoItem } from './bento-grid'

test('renders children inside grid', () => {
  render(
    <BentoGrid>
      <BentoItem>
        <span>Test content</span>
      </BentoItem>
    </BentoGrid>
  )
  expect(screen.getByText('Test content')).toBeInTheDocument()
})

test('BentoItem default has no col-span modifier', () => {
  const { container } = render(<BentoItem>content</BentoItem>)
  expect(container.firstChild).not.toHaveClass('md:col-span-2')
  expect(container.firstChild).not.toHaveClass('md:col-span-3')
})

test('BentoItem colSpan=2 applies md:col-span-2', () => {
  const { container } = render(<BentoItem colSpan={2}>content</BentoItem>)
  expect(container.firstChild).toHaveClass('md:col-span-2')
})

test('BentoItem colSpan=3 applies md:col-span-3', () => {
  const { container } = render(<BentoItem colSpan={3}>content</BentoItem>)
  expect(container.firstChild).toHaveClass('md:col-span-3')
})
