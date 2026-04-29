'use client'

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { getSettings, updateSettings } from '@/lib/api'

export default function SettingsPage() {
  const [provider] = useState<'gemini'>('gemini')
  const [apiKey, setApiKey] = useState('')
  const [maskedKey, setMaskedKey] = useState<string | null>(null)
  const [keySet, setKeySet] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showKey, setShowKey] = useState(false)

  useEffect(() => {
    getSettings()
      .then((s) => {
        setKeySet(s.api_key_set)
        setMaskedKey(s.api_key_masked)
      })
      .catch(() => toast.error('Erro ao carregar configurações'))
      .finally(() => setLoading(false))
  }, [])

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    if (!apiKey.trim()) return
    setSaving(true)
    try {
      await updateSettings(provider, apiKey)
      setKeySet(true)
      setMaskedKey(apiKey.slice(0, 8) + '...' + apiKey.slice(-4))
      setApiKey('')
      toast.success('API key salva com sucesso!')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Erro ao salvar')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">Configurações</h1>
        <p className="text-sm text-[var(--color-text-muted)] mt-1">
          Configure sua chave de API para usar o Aether.
        </p>
      </div>

      <div className="rounded-xl border border-[var(--color-card-border)] bg-[var(--color-card)] p-6 space-y-5">
        <div>
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">Provider</p>
          <div className="mt-2 flex items-center gap-2 rounded-lg border border-[var(--color-card-border)] bg-[var(--color-background)] px-3 py-2">
            <span className="text-sm text-[var(--color-text-primary)]">Gemini (Google)</span>
            <span className="ml-auto text-xs text-[var(--color-text-muted)]">gemini-2.0-flash</span>
          </div>
        </div>

        {keySet && maskedKey && (
          <div className="rounded-lg bg-green-950/40 border border-green-800/40 px-3 py-2 text-sm text-green-400">
            Chave configurada: <span className="font-mono">{maskedKey}</span>
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-4">
          <div className="space-y-2">
            <label className="block text-sm text-[var(--color-text-secondary)]">
              {keySet ? 'Substituir API key' : 'API key do Gemini'}
            </label>
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={keySet ? 'Nova chave...' : 'AIzaSy...'}
                className="w-full rounded-lg border border-[var(--color-card-border)] bg-[var(--color-background)] px-3 py-2 pr-10 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
              />
              <button
                type="button"
                onClick={() => setShowKey((v) => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]"
              >
                {showKey ? (
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                )}
              </button>
            </div>
            <p className="text-xs text-[var(--color-text-muted)]">
              Obtenha sua chave em{' '}
              <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-[var(--color-primary)] hover:underline">
                Google AI Studio
              </a>
            </p>
          </div>

          <button
            type="submit"
            disabled={saving || loading || !apiKey.trim()}
            className="w-full rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {saving ? 'Salvando...' : 'Salvar'}
          </button>
        </form>
      </div>
    </div>
  )
}
