import { describe, expect, it, vi } from 'vitest'
import { ApiError } from './errors'
import { createHttpBoardService } from './httpBoardService'

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('httpBoardService', () => {
  it('lists boards from GET /boards', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(
      jsonResponse([{ id: 'b1', name: 'Workshop', createdAt: 't', updatedAt: 't' }]),
    )
    const api = createHttpBoardService({
      baseUrl: 'http://localhost:8091',
      fetchImpl: fetchImpl as unknown as typeof fetch,
    })
    const boards = await api.listBoards()
    expect(fetchImpl).toHaveBeenCalledWith(
      'http://localhost:8091/boards',
      expect.objectContaining({ headers: expect.any(Object) }),
    )
    expect(boards[0].name).toBe('Workshop')
  })

  it('posts a move payload and maps 404 detail', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(
      jsonResponse({ detail: 'Card not found' }, 404),
    )
    const api = createHttpBoardService({
      baseUrl: 'http://localhost:8091/',
      fetchImpl: fetchImpl as unknown as typeof fetch,
    })
    await expect(
      api.moveCard('c1', { columnId: 'col', position: 0 }),
    ).rejects.toMatchObject({
      detail: 'Card not found',
      status: 404,
    } satisfies Partial<ApiError>)
    expect(fetchImpl).toHaveBeenCalledWith(
      'http://localhost:8091/cards/c1/move',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ columnId: 'col', position: 0 }),
      }),
    )
  })

  it('treats a network failure as Backend unreachable', async () => {
    const api = createHttpBoardService({
      fetchImpl: (async () => {
        throw new TypeError('Failed to fetch')
      }) as unknown as typeof fetch,
    })
    await expect(api.listBoards()).rejects.toMatchObject({
      detail: 'Backend unreachable',
      status: 503,
    })
  })
})
