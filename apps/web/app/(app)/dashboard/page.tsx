import { BentoGrid, BentoItem } from '@/components/bento/bento-grid'
import { SpotlightCard } from '@/components/ui/spotlight-card'
import { Skeleton } from '@/components/ui/skeleton'

export default function DashboardPage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">Dashboard</h1>

      <BentoGrid>
        <BentoItem colSpan={2}>
          <SpotlightCard className="p-6 h-48">
            <p className="text-sm text-[var(--color-text-muted)] mb-3">Objetivo</p>
            <Skeleton className="h-10 w-full" />
            <Skeleton className="mt-2 h-4 w-3/4" />
          </SpotlightCard>
        </BentoItem>

        <BentoItem>
          <SpotlightCard className="p-6 h-48">
            <p className="text-sm text-[var(--color-text-muted)] mb-3">Agentes ativos</p>
            <Skeleton className="h-8 w-16" />
          </SpotlightCard>
        </BentoItem>

        <BentoItem>
          <SpotlightCard className="p-6 h-40">
            <p className="text-sm text-[var(--color-text-muted)] mb-3">Skills</p>
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-4/6" />
            </div>
          </SpotlightCard>
        </BentoItem>

        <BentoItem colSpan={2}>
          <SpotlightCard className="p-6 h-40">
            <p className="text-sm text-[var(--color-text-muted)] mb-3">Runs recentes</p>
            <div className="space-y-2">
              <Skeleton className="h-8 w-full rounded-lg" />
              <Skeleton className="h-8 w-full rounded-lg" />
            </div>
          </SpotlightCard>
        </BentoItem>
      </BentoGrid>
    </div>
  )
}
