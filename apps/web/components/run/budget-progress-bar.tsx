interface BudgetProgressBarProps {
  totalTokens: number
  budgetLimit: number
  costUsd: number
}

function getBarColor(isExceeded: boolean, isWarning: boolean): string {
  if (isExceeded) return 'bg-error'
  if (isWarning) return 'bg-warning'
  return 'bg-primary'
}

export function BudgetProgressBar({ totalTokens, budgetLimit, costUsd }: Readonly<BudgetProgressBarProps>) {
  const percent = budgetLimit > 0 ? Math.min((totalTokens / budgetLimit) * 100, 100) : 0
  const isExceeded = percent >= 100
  const isWarning = percent >= 80 && !isExceeded
  const barColor = getBarColor(isExceeded, isWarning)

  return (
    <div className="flex items-center gap-3 text-xs text-text-secondary w-full">
      <div className="flex-1 h-1.5 bg-card-border rounded-full overflow-hidden min-w-0">
        <div
          data-testid="budget-bar"
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className="whitespace-nowrap tabular-nums">
        {totalTokens.toLocaleString('pt-BR')} / {budgetLimit.toLocaleString('pt-BR')} tokens
      </span>
      <span className="whitespace-nowrap tabular-nums text-text-muted">
        ${costUsd.toFixed(4)}
      </span>
    </div>
  )
}
