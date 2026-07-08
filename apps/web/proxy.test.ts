import { describe, it, expect } from 'vitest'
import { isAppRoute, isAuthRoute } from './proxy'

describe('isAppRoute', () => {
  it.each(['/dashboard', '/run', '/run/abc-123', '/history', '/settings', '/admin'])(
    '%s é uma rota protegida',
    (path) => {
      expect(isAppRoute(path)).toBe(true)
    }
  )

  it.each(['/login', '/signup', '/forgot-password', '/reset-password', '/'])(
    '%s não é uma rota protegida',
    (path) => {
      expect(isAppRoute(path)).toBe(false)
    }
  )
})

describe('isAuthRoute', () => {
  it('/login e /signup são rotas de auth', () => {
    expect(isAuthRoute('/login')).toBe(true)
    expect(isAuthRoute('/signup')).toBe(true)
  })

  it('/forgot-password não é redirecionada como rota de auth', () => {
    expect(isAuthRoute('/forgot-password')).toBe(false)
  })

  it('/dashboard não é rota de auth', () => {
    expect(isAuthRoute('/dashboard')).toBe(false)
  })
})
