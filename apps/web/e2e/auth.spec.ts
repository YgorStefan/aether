import { expect, test } from '@playwright/test'
import { TEST_PASSWORD, login, logout, signup, uniqueEmail } from './helpers'

test('redireciona usuário não autenticado para /login', async ({ page }) => {
  await page.goto('/dashboard')
  await page.waitForURL('**/login')
  await expect(page).toHaveURL(/\/login/)
})

test('signup cria a conta e faz login com sucesso', async ({ page }) => {
  const email = uniqueEmail('signup')
  await signup(page, email)

  // Confirmação de email desabilitada no Supabase local: a sessão já existe após o
  // signup, então a navegação de volta a /login é interceptada pelo proxy e redireciona
  // para /dashboard. Isso valida o pipeline completo (signup -> cookie de sessão -> proxy).
  await page.getByText('Ir para login').click()
  await page.waitForURL('**/dashboard')
  await expect(page).toHaveURL(/\/dashboard/)
})

test('login com credenciais inválidas mostra erro', async ({ page }) => {
  await page.goto('/login')
  await page.getByPlaceholder('seu@email.com').fill('inexistente@e2e.local')
  await page.getByPlaceholder('••••••••').fill('senha-errada')
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page.getByText(/inválid|Invalid/i)).toBeVisible()
})

test('login, navegação autenticada e logout', async ({ page }) => {
  const email = uniqueEmail('login')
  await signup(page, email)

  // Signup já deixa uma sessão ativa (confirmações desabilitadas localmente); encerra
  // essa sessão para exercitar o formulário de login "de verdade" com as credenciais.
  await page.goto('/dashboard')
  await logout(page)

  await login(page, email)
  await expect(page.getByText(email)).toBeVisible()
  await expect(page.getByRole('link', { name: 'Histórico' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Admin' })).toHaveCount(0)

  await logout(page)

  // Sessão encerrada: rota protegida volta a redirecionar.
  await page.goto('/dashboard')
  await page.waitForURL('**/login')
})

test('esqueci a senha envia o link de redefinição', async ({ page }) => {
  const email = uniqueEmail('forgot')
  await signup(page, email)

  await page.goto('/forgot-password')
  await page.getByPlaceholder('seu@email.com').fill(email)
  await page.getByRole('button', { name: 'Enviar link' }).click()
  await expect(
    page.getByText('Se existir uma conta com esse email, enviamos um link para redefinir a senha.')
  ).toBeVisible()
})

test('acessar /reset-password sem sessão de recuperação mostra erro ao tentar salvar', async ({ page }) => {
  await page.goto('/reset-password')
  await page.getByPlaceholder('mínimo 6 caracteres').fill(TEST_PASSWORD)
  await page.getByRole('button', { name: 'Redefinir senha' }).click()
  await expect(page.getByText(/não foi possível redefinir|session|Auth session missing/i)).toBeVisible()
})
