import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['html', { open: 'never' }], ['list']],
  timeout: 30_000,
  use: {
    baseURL: 'http://localhost:3100',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: [
    {
      command: String.raw`venv\Scripts\python.exe -m uvicorn api.main:app --port 8000`,
      cwd: '../server',
      url: 'http://localhost:8000/api/v1/health',
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      // Porta 3000 costuma estar ocupada por outros projetos locais; 3100 evita conflito.
      command: 'pnpm dev',
      cwd: '.',
      env: { PORT: '3100' },
      url: 'http://localhost:3100',
      reuseExistingServer: true,
      timeout: 60_000,
    },
  ],
})
