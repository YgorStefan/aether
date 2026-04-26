import Link from 'next/link'

export default function LandingPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-[var(--color-background)] px-4 text-center">
      <h1 className="text-4xl font-bold text-[var(--color-text-primary)] mb-4">
        Aether OS
      </h1>
      <p className="text-lg text-[var(--color-text-secondary)] mb-8 max-w-md">
        Orquestrador de agentes de IA. Defina um objetivo, assista os agentes colaborando em tempo real.
      </p>
      <Link
        href="/login"
        className="rounded-lg bg-[var(--color-primary)] px-6 py-3 text-sm font-medium text-white transition-opacity hover:opacity-90"
      >
        Começar
      </Link>
    </main>
  )
}
