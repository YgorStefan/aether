import Link from 'next/link'

export default function LandingPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-background px-4 text-center">
      <h1 className="text-4xl font-bold text-text-primary mb-4">
        Aether
      </h1>
      <p className="text-lg text-text-secondary mb-8 max-w-md">
        Orquestrador de agentes de IA. Defina um objetivo, assista os agentes colaborando em tempo real.
      </p>
      <Link
        href="/login"
        className="rounded-lg bg-primary px-6 py-3 text-sm font-medium text-white transition-opacity hover:opacity-90"
      >
        Começar
      </Link>
    </main>
  )
}
