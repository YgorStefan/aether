// Script de UAT manual: navega pela aplicação local como um usuário real faria,
// tirando screenshots de cada etapa. Não é um teste automatizado (sem asserts) —
// é um passeio guiado para inspeção visual/manual da sessão.
import { chromium } from '@playwright/test'
import { mkdirSync } from 'node:fs'

const BASE = 'http://localhost:3100'
const OUT = 'uat-screenshots'
mkdirSync(OUT, { recursive: true })

const email = `uat-${Date.now()}@e2e.local`
const password = 'senha-teste-123' // NOSONAR - senha de fixture usada apenas neste script manual local

let step = 0
async function shot(page, name) {
  step += 1
  const filename = `${OUT}/${String(step).padStart(2, '0')}-${name}.png`
  await page.screenshot({ path: filename, fullPage: true })
  console.log(`[${step}] ${name} -> ${filename}`)
}

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } })

console.log('== 1. Landing / redirecionamento para login ==')
await page.goto(BASE)
await page.waitForLoadState('networkidle')
await shot(page, 'landing-redirect-login')

console.log('== 2. Tela de signup ==')
await page.goto(`${BASE}/signup`)
await shot(page, 'signup-page')
await page.getByPlaceholder('seu@email.com').fill(email)
await page.getByPlaceholder('mínimo 6 caracteres').fill(password)
await page.getByRole('button', { name: 'Criar conta' }).click()
await page.getByText('Verifique seu email para confirmar a conta.').waitFor()
await shot(page, 'signup-success-message')

console.log('== 3. Dashboard após signup (auto-login local) ==')
await page.goto(`${BASE}/dashboard`)
await page.waitForURL('**/dashboard')
await shot(page, 'dashboard-empty')

console.log('== 4. Criar um run (objetivo simples) ==')
await page.getByPlaceholder(/Descreva seu objetivo/).fill('Verificar o horário atual do sistema para o UAT manual')
await shot(page, 'dashboard-objective-filled')
await page.getByRole('button', { name: 'Executar' }).click()
await page.waitForURL('**/run/**', { timeout: 15_000 })
await shot(page, 'run-page-started')

console.log('== 5. Acompanhar execução via SSE até concluir ==')
await page.getByText('Concluído', { exact: true }).first().waitFor({ timeout: 20_000 })
await shot(page, 'run-page-completed')

console.log('== 6. Histórico de runs ==')
await page.goto(`${BASE}/history`)
await page.waitForLoadState('networkidle')
await shot(page, 'history-page')

console.log('== 7. Configurações (settings) ==')
await page.goto(`${BASE}/settings`)
await page.waitForLoadState('networkidle')
await shot(page, 'settings-page')

console.log('== 8. Acesso negado ao painel admin (usuário comum) ==')
await page.goto(`${BASE}/admin`)
await page.waitForURL('**/dashboard', { timeout: 10_000 }).catch(() => {})
await shot(page, 'admin-denied-redirect')

console.log('== 9. Esqueci a senha ==')
await page.goto(`${BASE}/forgot-password`)
await shot(page, 'forgot-password-page')
await page.getByPlaceholder('seu@email.com').fill(email)
await page.getByRole('button', { name: /Enviar/ }).click()
await shot(page, 'forgot-password-sent')

console.log('== 10. Logout ==')
await page.goto(`${BASE}/dashboard`)
await page.getByRole('button', { name: 'Sair' }).click()
await page.waitForURL('**/login')
await shot(page, 'logout-back-to-login')

console.log('== 11. Rota protegida sem sessão redireciona para login ==')
await page.goto(`${BASE}/history`)
await page.waitForURL('**/login')
await shot(page, 'protected-route-redirects')

await browser.close()
console.log('\nUAT walkthrough concluído. Screenshots em', OUT)
