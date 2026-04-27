'use client'

import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import type { RunEvent } from '@/hooks/use-run-stream'
import { getHighlighter } from '@/lib/highlighter'
import type { Highlighter } from 'shiki'

const EVENT_LABELS: Partial<Record<RunEvent['type'], string>> = {
  agent_started:  'Agente iniciado',
  task_started:   'Tarefa iniciada',
  task_completed: 'Tarefa concluída',
  skill_called:   'Skill chamada',
  hitl_required:  'Aprovação necessária',
  run_completed:  'Run concluído',
  run_failed:     'Run falhou',
  budget_warning: 'Aviso de budget',
}

function eventToMarkdown(event: RunEvent): string {
  const p = event.payload as Record<string, string | number | undefined>
  switch (event.type) {
    case 'agent_started':
      return `Agente **${p.agent_name ?? 'desconhecido'}** iniciado.`
    case 'task_started':
      return `Iniciando: ${p.task ?? ''}`
    case 'task_completed':
      return `Tarefa **${p.status === 'done' ? 'concluída' : 'falhou'}**: ${p.task ?? ''}`
    case 'skill_called':
      return `Skill **${p.skill ?? ''}** chamada.`
    case 'hitl_required':
      return `⚠️ Aguardando aprovação para: **${p.skill ?? ''}**`
    case 'run_completed':
      return 'Concluído com sucesso.'
    case 'run_failed':
      return `**Falha:** ${p.error ?? 'Erro desconhecido'}`
    case 'budget_warning':
      return `Aviso de budget: custo atual $${Number(p.cost_usd ?? 0).toFixed(4)}.`
    default:
      return JSON.stringify(p)
  }
}

export function MessageList({ events }: { events: RunEvent[] }) {
  const [highlighter, setHighlighter] = useState<Highlighter | null>(null)

  useEffect(() => {
    getHighlighter().then(setHighlighter).catch(() => null)
  }, [])

  if (events.length === 0) {
    return (
      <p className="text-sm text-[var(--color-text-muted)] text-center py-8">
        Aguardando agente...
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {events.map((event, i) => (
        <div key={i} className="rounded-lg border border-[var(--color-card-border)] bg-[var(--color-card)] p-4">
          <p className="text-xs font-medium text-[var(--color-text-muted)] mb-2 uppercase tracking-wide">
            {EVENT_LABELS[event.type] ?? event.type}
          </p>
          <div className="text-sm text-[var(--color-text-primary)]">
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                strong: ({ children }) => (
                  <strong className="font-semibold text-[var(--color-text-primary)]">{children}</strong>
                ),
                code(props) {
                  const { children, className } = props
                  const match = /language-(\w+)/.exec(className ?? '')
                  const code = String(children).trim()
                  if (match && highlighter) {
                    const html = highlighter.codeToHtml(code, {
                      lang: match[1],
                      theme: 'github-dark',
                    })
                    return (
                      <div
                        dangerouslySetInnerHTML={{ __html: html }}
                        className="rounded-lg overflow-x-auto text-xs my-2 [&_pre]:p-4"
                      />
                    )
                  }
                  return (
                    <code className="bg-[#1f1f1f] px-1.5 py-0.5 rounded text-xs font-mono">
                      {children}
                    </code>
                  )
                },
              }}
            >
              {eventToMarkdown(event)}
            </ReactMarkdown>
          </div>
        </div>
      ))}
    </div>
  )
}
