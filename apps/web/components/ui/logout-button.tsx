'use client'

import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase'

export function LogoutButton() {
  const router = useRouter()

  async function handleLogout() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/login')
  }

  return (
    <button
      onClick={handleLogout}
      className="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors px-2 py-1 rounded hover:bg-[var(--color-card)] min-h-[44px]"
    >
      Sair
    </button>
  )
}
