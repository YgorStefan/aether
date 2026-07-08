import { expect, test } from '@playwright/test'
import { promoteToAdmin, signup, signupAndLogin, uniqueEmail } from './helpers'

test('usuário comum não vê o link Admin e é redirecionado ao acessar /admin', async ({ page }) => {
  const email = uniqueEmail('nonadmin')
  await signupAndLogin(page, email)

  await expect(page.getByRole('link', { name: 'Admin' })).toHaveCount(0)

  await page.goto('/admin')
  await page.waitForURL('**/dashboard')
})

test('usuário promovido a admin vê o link Admin e o painel com usuários e runs', async ({ page }) => {
  const email = uniqueEmail('admin')
  await signup(page, email)
  promoteToAdmin(email)

  await page.goto('/dashboard')
  await page.waitForURL('**/dashboard')
  await expect(page.getByRole('link', { name: 'Admin' })).toBeVisible()

  await page.getByRole('link', { name: 'Admin' }).click()
  await page.waitForURL('**/admin')
  await expect(page.getByText(/Usuários \(\d+\)/)).toBeVisible({ timeout: 15_000 })
  await expect(page.getByText(/Runs recentes \(\d+\)/)).toBeVisible()
  await expect(page.getByText(email).first()).toBeVisible()
})
