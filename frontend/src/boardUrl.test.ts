import { describe, expect, it } from 'vitest'
import { readBoardIdFromLocation } from './boardUrl'

describe('boardUrl', () => {
  it('reads the join-link board id', () => {
    expect(readBoardIdFromLocation({ search: '?board=abc-123' })).toBe('abc-123')
    expect(readBoardIdFromLocation({ search: '' })).toBeNull()
  })
})
