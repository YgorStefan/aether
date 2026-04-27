import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

vi.mock('@/lib/api', () => ({
  getSkills: vi.fn().mockResolvedValue([
    { name: 'web_search', description: 'Busca na web', parameters_schema: {}, requires_approval: false },
    { name: 'code_interpreter', description: 'Executa código', parameters_schema: {}, requires_approval: true },
  ]),
}))

import { SkillsCatalog } from './skills-catalog'

describe('SkillsCatalog', () => {
  it('mostra skeleton enquanto carrega', () => {
    const { container } = render(<SkillsCatalog />)
    // Skeleton elements existem durante loading
    const skeletons = container.querySelectorAll('[class*="animate-pulse"]')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('renderiza skills após carregar', async () => {
    render(<SkillsCatalog />)
    await waitFor(() => {
      expect(screen.getByText('web_search')).toBeInTheDocument()
      expect(screen.getByText('code_interpreter')).toBeInTheDocument()
    })
  })

  it('mostra badge "aprovação" em skills com requires_approval', async () => {
    render(<SkillsCatalog />)
    await waitFor(() => {
      expect(screen.getByText('aprovação')).toBeInTheDocument()
    })
  })
})
