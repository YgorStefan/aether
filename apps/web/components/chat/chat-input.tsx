'use client'

import { useRef, useState } from 'react'

interface ChatInputProps {
  onSubmit: (objective: string) => Promise<void>
  onCancel?: () => void
  disabled?: boolean
}

export function ChatInput({ onSubmit, onCancel, disabled = false }: ChatInputProps) {
  const [value, setValue] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const canSubmit = value.trim().length >= 10 && !submitting && !disabled

  async function handleSubmit(e?: React.FormEvent) {
    e?.preventDefault()
    if (!canSubmit) return
    const objective = value.trim()
    setSubmitting(true)
    try {
      await onSubmit(objective)
      setValue('')
    } finally {
      setSubmitting(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault()
      handleSubmit()
    }
    if (e.key === 'Escape' && onCancel) {
      onCancel()
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Descreva seu objetivo… (mín. 10 caracteres)"
        rows={3}
        disabled={submitting || disabled}
        className="w-full resize-none rounded-lg border border-[var(--color-card-border)] bg-[var(--color-card)] px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-primary)] disabled:opacity-50 min-h-[44px]"
      />
      <div className="flex items-center justify-between">
        <span className="text-xs text-[var(--color-text-muted)]">
          {value.length}/500 · Cmd+Enter para enviar
        </span>
        <button
          type="submit"
          disabled={!canSubmit}
          className="px-4 py-2 rounded-lg bg-[var(--color-primary)] text-white text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-purple-400 transition-colors min-h-[44px]"
        >
          {submitting ? 'Enviando…' : 'Executar'}
        </button>
      </div>
    </form>
  )
}
