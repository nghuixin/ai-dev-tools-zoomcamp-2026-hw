import { compose, defaultBaseURL, waitUntilReady } from './compose'

export default async function globalSetup() {
  if (!process.env.E2E_BASE_URL) {
    compose('up', '-d', '--build')
  }
  await waitUntilReady(defaultBaseURL)
}
