import { compose } from './compose'

export default async function globalTeardown() {
  if (process.env.E2E_BASE_URL || process.env.E2E_KEEP_STACK === '1') return
  compose('down', '-v')
}
