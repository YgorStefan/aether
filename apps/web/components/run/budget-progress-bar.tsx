interface BudgetProgressBarProps {
  totalTokens: number
  budgetLimit: number
  costUsd: number
}

export function BudgetProgressBar({ totalTokens, budgetLimit, costUsd }: BudgetProgressBarProps) {
  const percent = budgetLimit > 0 ? Math.min((totalTokens / budgetLimit) * 100, 100) : 0
  const isExceeded = percent >= 100
  const isWarning = percent >= 80 && !isExceeded

  const barColor = isExceeded
    ? 'bg-[#ef4444]'
    : isWarning
    ? 'bg-[#fbbf24]'
    : 'bg-[#a855f7]'

  return (
    <div className="flex items-center gap-3 text-xs text-[#94a3b8] w-full">
      <div className="flex-1 h-1.5 bg-[#1f1f1f] rounded-full overflow-hidden min-w-0">
        <div
          data-testid="budget-bar"
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className="whitespace-nowrap tabular-nums">
        {totalTokens.toLocaleString('pt-BR')} / {budgetLimit.toLocaleString('pt-BR')} tokens
      </span>
      <span className="whitespace-nowrap tabular-nums text-[#64748b]">
        ${costUsd.toFixed(4)}
      </span>
    </div>
  )
}
