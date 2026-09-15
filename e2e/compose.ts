import { execFileSync } from 'node:child_process'
import path from 'node:path'

export const REPO_ROOT = path.resolve(__dirname, '..')
export const PROJECT = process.env.E2E_COMPOSE_PROJECT ?? 'kanban-e2e'
export const APP_PORT = process.env.E2E_APP_PORT ?? '18092'
export const POSTGRES_PORT = process.env.E2E_POSTGRES_PORT ?? '15433'
export const defaultBaseURL = process.env.E2E_BASE_URL ?? `http://127.0.0.1:${APP_PORT}`

export function composeEnv(): NodeJS.ProcessEnv {
  return {
    ...process.env,
    APP_PORT,
    POSTGRES_PORT,
  }
}

export function compose(...args: string[]) {
  execFileSync('docker', ['compose', '-f', 'docker-compose.yml', '-p', PROJECT, ...args], {
    cwd: REPO_ROOT,
    env: composeEnv(),
    stdio: 'inherit',
  })
}

export async function waitUntilReady(baseURL: string, timeoutMs = 240_000) {
  const deadline = Date.now() + timeoutMs
  let lastError = 'no attempt yet'
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${baseURL}/health`)
      if (response.status < 500) return
      lastError = `HTTP ${response.status}`
    } catch (error) {
      lastError = error instanceof Error ? error.message : String(error)
    }
    await new Promise((resolve) => setTimeout(resolve, 1000))
  }
  throw new Error(`Compose stack at ${baseURL} was not ready: ${lastError}`)
}
