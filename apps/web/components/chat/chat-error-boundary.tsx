'use client'

import { Component, type ReactNode } from 'react'

export class ChatErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(): { hasError: boolean } {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center p-8 text-center">
          <p className="text-sm text-[var(--color-text-secondary)] mb-4">Algo deu errado.</p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="px-3 py-2 rounded-lg border border-[var(--color-card-border)] text-sm text-[var(--color-text-primary)] hover:border-[var(--color-primary)] transition-colors min-h-[44px]"
          >
            Tentar novamente
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
