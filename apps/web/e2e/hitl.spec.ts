import { expect, test } from '@playwright/test'
import { signupAndLogin, uniqueEmail } from './helpers'

test('run que exige aprovação humana (HITL) pausa, aguarda e conclui após aprovar', async ({ page }) => {
  const email = uniqueEmail('hitl')
  await signupAndLogin(page, email)

  // "arquivo" no objetivo faz o AutoMockLLMAdapter selecionar a skill file_writer,
  // que exige aprovação humana (requires_approval=True).
  const objective = 'Gerar um arquivo de resumo do teste automatizado'
  await page.getByPlaceholder(/Descreva seu objetivo/).fill(objective)
  await page.getByRole('button', { name: 'Executar' }).click()
  await page.waitForURL('**/run/**')

  await expect(page.getByText('⏸ Aprovação necessária')).toBeVisible({ timeout: 15_000 })
  await expect(page.getByText('file_writer').first()).toBeVisible()

  await page.getByRole('button', { name: 'Aprovar' }).click()
  await expect(page.getByText('Concluído', { exact: true }).first()).toBeVisible({ timeout: 20_000 })
})

test('run com skill HITL rejeitada não conclui com sucesso', async ({ page }) => {
  const email = uniqueEmail('hitlreject')
  await signupAndLogin(page, email)

  const objective = 'Gerar outro arquivo de teste para validar rejeicao'
  await page.getByPlaceholder(/Descreva seu objetivo/).fill(objective)
  await page.getByRole('button', { name: 'Executar' }).click()
  await page.waitForURL('**/run/**')

  await expect(page.getByText('⏸ Aprovação necessária')).toBeVisible({ timeout: 15_000 })
  await page.getByRole('button', { name: 'Rejeitar' }).click()
  await expect(page.getByText('Falhou', { exact: true }).first()).toBeVisible({ timeout: 20_000 })
})
