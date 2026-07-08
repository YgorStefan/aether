import { execSync } from 'node:child_process'
import { randomInt } from 'node:crypto'
import type { Page } from '@playwright/test'

export function uniqueEmail(prefix: string): string {
  return `${prefix}-${Date.now()}-${randomInt(100000)}@e2e.local`
}

export const TEST_PASSWORD = 'senha-teste-123' // NOSONAR - senha de fixture usada apenas em testes e2e locais

export async function signup(page: Page, email: string, password = TEST_PASSWORD): Promise<void> {
  await page.goto('/signup')
  await page.getByPlaceholder('seu@email.com').fill(email)
  await page.getByPlaceholder('mínimo 6 caracteres').fill(password)
  await page.getByRole('button', { name: 'Criar conta' }).click()
  await page.getByText('Verifique seu email para confirmar a conta.').waitFor()
}

export async function login(page: Page, email: string, password = TEST_PASSWORD): Promise<void> {
  await page.goto('/login')
  await page.getByPlaceholder('seu@email.com').fill(email)
  await page.getByPlaceholder('••••••••').fill(password)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await page.waitForURL('**/dashboard')
}

/**
 * Cria a conta e navega para o dashboard. Confirmações de email estão desabilitadas no
 * Supabase local, então o signup já retorna uma sessão ativa — não é preciso (e o
 * proxy impediria) passar pela tela de login de novo em seguida.
 */
export async function signupAndLogin(page: Page, email: string, password = TEST_PASSWORD): Promise<void> {
  await signup(page, email, password)
  await page.goto('/dashboard')
  await page.waitForURL('**/dashboard')
}

export async function logout(page: Page): Promise<void> {
  await page.getByRole('button', { name: 'Sair' }).click()
  await page.waitForURL('**/login')
}

/** Promove um usuário a admin diretamente no Postgres local (equivalente ao SQL manual documentado). */
export function promoteToAdmin(email: string): void {
  execSync(
    `docker exec supabase_db_aether psql -U postgres -d postgres -c "UPDATE profiles SET role='admin' WHERE email='${email}';"`,
    { stdio: 'pipe' }
  )
}
