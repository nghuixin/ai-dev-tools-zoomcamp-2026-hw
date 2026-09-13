import { describe, expect, it } from 'vitest'

const sources = import.meta.glob(['../**/*.ts', '../**/*.tsx'], {
  eager: true,
  query: '?raw',
  import: 'default',
}) as Record<string, string>

describe('service boundary', () => {
  it('keeps fetch and XMLHttpRequest inside the services layer', () => {
    const offenders = Object.entries(sources)
      .filter(([path]) => !path.includes('/services/') && !path.includes('.test.'))
      .filter(([, source]) => /\bfetch\s*\(|XMLHttpRequest|axios\b/.test(source))
      .map(([path]) => path)

    expect(offenders).toEqual([])
  })
})
