import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    globals: true,
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '.'),
      react: path.resolve(__dirname, '../../node_modules/.pnpm/react@19.2.4/node_modules/react'),
      'react-dom': path.resolve(__dirname, '../../node_modules/.pnpm/react-dom@19.2.4_react@19.2.4/node_modules/react-dom'),
    },
    dedupe: ['react', 'react-dom'],
  },
})
