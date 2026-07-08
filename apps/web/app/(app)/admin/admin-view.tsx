'use client'

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { getAdminRuns, getAdminUsers, type AdminRun, type AdminUser } from '@/lib/api'
import { StatusBadge } from '@/components/run/status-badge'

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export function AdminView() {
  const [users, setUsers] = useState<AdminUser[]>([])
  const [runs, setRuns] = useState<AdminRun[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getAdminUsers(), getAdminRuns()])
      .then(([u, r]) => {
        setUsers(u)
        setRuns(r)
      })
      .catch(() => toast.error('Erro ao carregar dados do painel admin'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <p className="text-sm text-text-muted">Carregando...</p>
  }

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <h2 className="text-sm font-medium text-text-secondary">
          Usuários ({users.length})
        </h2>
        <div className="rounded-xl border border-card-border bg-card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-text-muted border-b border-card-border">
                <th className="p-3 font-medium">Email</th>
                <th className="p-3 font-medium">Role</th>
                <th className="p-3 font-medium">Runs</th>
                <th className="p-3 font-medium">Cadastro</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.user_id} className="border-b border-card-border last:border-0">
                  <td className="p-3 text-text-primary">{u.email}</td>
                  <td className="p-3 text-text-muted">{u.role}</td>
                  <td className="p-3 text-text-muted tabular-nums">{u.run_count}</td>
                  <td className="p-3 text-text-muted">{formatDate(u.created_at)}</td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td className="p-3 text-text-muted" colSpan={4}>Nenhum usuário ainda.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-text-secondary">
          Runs recentes ({runs.length})
        </h2>
        <div className="rounded-xl border border-card-border bg-card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-text-muted border-b border-card-border">
                <th className="p-3 font-medium">Objetivo</th>
                <th className="p-3 font-medium">Usuário</th>
                <th className="p-3 font-medium">Status</th>
                <th className="p-3 font-medium">Tokens</th>
                <th className="p-3 font-medium">Custo</th>
                <th className="p-3 font-medium">Criado em</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id} className="border-b border-card-border last:border-0">
                  <td className="p-3 text-text-primary max-w-xs truncate">{r.objective}</td>
                  <td className="p-3 text-text-muted">{r.user_email}</td>
                  <td className="p-3"><StatusBadge status={r.status} /></td>
                  <td className="p-3 text-text-muted tabular-nums">{r.total_tokens.toLocaleString('pt-BR')}</td>
                  <td className="p-3 text-text-muted tabular-nums">${r.cost_usd.toFixed(4)}</td>
                  <td className="p-3 text-text-muted">{formatDate(r.created_at)}</td>
                </tr>
              ))}
              {runs.length === 0 && (
                <tr>
                  <td className="p-3 text-text-muted" colSpan={6}>Nenhuma run ainda.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
