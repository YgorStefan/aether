import { expect, test } from '@playwright/test'
import { TEST_PASSWORD, signupAndLogin, uniqueEmail } from './helpers'

test('salva a API key nas configurações e ela aparece mascarada', async ({ page }) => {
  const email = uniqueEmail('settings')
  await signupAndLogin(page, email)

  await page.goto('/settings')
  await page.getByPlaceholder('AIzaSy...').fill('AIzaSyE2E1234567890teste')
  await page.getByRole('button', { name: 'Salvar' }).click()

  await expect(page.getByText(/Chave configurada:/)).toBeVisible()
  await expect(page.getByText(/AIzaSyE2\.\.\.este/)).toBeVisible()
})

test('exclui a conta e impede login subsequente', async ({ page }) => {
  const email = uniqueEmail('delete')
  await signupAndLogin(page, email)

  await page.goto('/settings')
  await page.getByRole('button', { name: 'Excluir conta' }).click()
  await page.getByRole('button', { name: 'Confirmar exclusão' }).click()

  await page.waitForURL('**/login')

  await page.getByPlaceholder('seu@email.com').fill(email)
  await page.getByPlaceholder('••••••••').fill(TEST_PASSWORD)
  await page.getByRole('button', { name: 'Entrar' }).click()
  await expect(page.getByText(/inválid|Invalid/i)).toBeVisible()
})
