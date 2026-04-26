'use client'

import { createClient } from '@/lib/supabase'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState } from 'react'

export default function SignupPage() {
  const router = useRouter()
  const supabase = createClient()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
    })
    if (error) {
      setError(error.message)
      setLoading(false)
    } else {
      setSuccess(true)
    }
  }

  if (success) {
    return (
      <div className="w-full max-w-sm space-y-4 text-center">
        <p className="text-[var(--color-success)] text-sm">
          Verifique seu email para confirmar a conta.
        </p>
        <Link href="/login" className="text-xs text-[var(--color-primary)] hover:underline">
          Ir para login
        </Link>
      </div>
    )
  }

  return (
    <div className="w-full max-w-sm space-y-6">
      <div className="space-y-1 text-center">
        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">Criar conta</h1>
        <p className="text-sm text-[var(--color-text-muted)]">Junte-se ao Aether OS</p>
      </div>

      <form onSubmit={handleSignup} className="space-y-4">
        <div className="space-y-2">
          <label className="block text-sm text-[var(--color-text-secondary)]">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-[var(--color-card-border)] bg-[var(--color-card)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
            placeholder="seu@email.com"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm text-[var(--color-text-secondary)]">Senha</label>
          <input
            type="password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-[var(--color-card-border)] bg-[var(--color-card)] px-3 py-2 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
            placeholder="mínimo 6 caracteres"
          />
        </div>

        {error && <p className="text-xs text-[var(--color-error)]">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {loading ? 'Criando conta...' : 'Criar conta'}
        </button>
      </form>

      <p className="text-center text-xs text-[var(--color-text-muted)]">
        Já tem conta?{' '}
        <Link href="/login" className="text-[var(--color-primary)] hover:underline">
          Entrar
        </Link>
      </p>
    </div>
  )
}
