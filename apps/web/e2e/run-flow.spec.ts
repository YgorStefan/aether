import { expect, test } from '@playwright/test'
import { signupAndLogin, uniqueEmail } from './helpers'

test.describe.configure({ mode: 'serial' })

test('cria um run, acompanha a execução via SSE e vê o resultado concluído', async ({ page }) => {
  const email = uniqueEmail('run')
  await signupAndLogin(page, email)

  const objective = 'Verificar o horário atual do sistema para o teste automatizado E2E'
  await page.getByPlaceholder(/Descreva seu objetivo/).fill(objective)
  await page.getByRole('button', { name: 'Executar' }).click()

  await page.waitForURL('**/run/**', { timeout: 15_000 })
  await expect(page.getByText(objective)).toBeVisible()

  // Modo mock resolve para a skill time_manager (sem aprovação), então o run deve
  // concluir sozinho dentro do timeout de HITL configurado localmente.
  await expect(page.getByText('Concluído', { exact: true }).first()).toBeVisible({ timeout: 20_000 })
})

test('run concluído aparece na página de histórico após reload', async ({ page }) => {
  const email = uniqueEmail('history')
  await signupAndLogin(page, email)

  const objective = 'Confirmar horario atual para validar historico apos reload'
  await page.getByPlaceholder(/Descreva seu objetivo/).fill(objective)
  await page.getByRole('button', { name: 'Executar' }).click()
  await page.waitForURL('**/run/**')
  await expect(page.getByText('Concluído', { exact: true }).first()).toBeVisible({ timeout: 20_000 })

  await page.goto('/history')
  await expect(page.getByText(objective)).toBeVisible()
})
