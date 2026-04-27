'use client'

import { useSkills } from '@/hooks/use-skills'
import { Skeleton } from '@/components/ui/skeleton'

export function SkillsCatalog() {
  const { skills, loading } = useSkills()

  if (loading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-4/6" />
      </div>
    )
  }

  if (skills.length === 0) {
    return <p className="text-xs text-[var(--color-text-muted)]">Nenhuma skill disponível.</p>
  }

  return (
    <div className="space-y-3">
      {skills.map(skill => (
        <div key={skill.name} className="flex items-start gap-2">
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-[var(--color-text-primary)]">{skill.name}</p>
            <p className="text-xs text-[var(--color-text-muted)] mt-0.5 truncate">{skill.description}</p>
          </div>
          {skill.requires_approval && (
            <span className="shrink-0 text-[10px] px-1.5 py-0.5 rounded bg-yellow-950 text-[var(--color-warning)]">
              aprovação
            </span>
          )}
        </div>
      ))}
    </div>
  )
}
