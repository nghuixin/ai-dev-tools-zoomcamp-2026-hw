import { describe, expect, it } from 'vitest'
import { ApiError } from './errors'
import { createMockBoardService, DEFAULT_COLUMN_TITLES } from './mockBoardService'
import { memoryKv } from './storage'

function service() {
  return createMockBoardService({ kv: memoryKv() })
}

describe('mockBoardService', () => {
  it('creates a board seeded with default columns', async () => {
    const api = service()
    const board = await api.createBoard({ name: ' Workshop ' })
    expect(board.name).toBe('Workshop')
    expect(board.columns.map((column) => column.title)).toEqual([...DEFAULT_COLUMN_TITLES])
    expect(board.columns.every((column) => column.position === board.columns.indexOf(column))).toBe(
      true,
    )
  })

  it('rejects invalid names and titles', async () => {
    const api = service()
    await expect(api.createBoard({ name: '   ' })).rejects.toBeInstanceOf(ApiError)
    const board = await api.createBoard({ name: 'Ok' })
    await expect(api.createColumn(board.id, { title: '' })).rejects.toMatchObject({
      detail: 'Column title must be 1–60 characters',
    })
    await expect(
      api.createCard(board.columns[0].id, { title: 'x'.repeat(201) }),
    ).rejects.toBeInstanceOf(ApiError)
  })

  it('lists boards with the most recently updated first', async () => {
    let tick = 0
    const api = createMockBoardService({
      kv: memoryKv(),
      now: () => {
        tick += 1
        return `2026-09-12T00:00:0${tick}.000Z`
      },
    })
    await api.createBoard({ name: 'Older' })
    const newer = await api.createBoard({ name: 'Newer' })
    const list = await api.listBoards()
    expect(list[0].id).toBe(newer.id)
  })

  it('renames a board and loads the nested snapshot', async () => {
    const api = service()
    const created = await api.createBoard({ name: 'Alpha' })
    const updated = await api.updateBoard(created.id, { name: 'Beta' })
    expect(updated.name).toBe('Beta')
    const loaded = await api.getBoard(created.id)
    expect(loaded.name).toBe('Beta')
    expect(loaded.columns).toHaveLength(3)
  })

  it('cascades delete from board to columns and cards', async () => {
    const api = service()
    const board = await api.createBoard({ name: 'Temp' })
    await api.createCard(board.columns[0].id, { title: 'Task' })
    await api.deleteBoard(board.id)
    await expect(api.getBoard(board.id)).rejects.toMatchObject({ status: 404 })
    expect(await api.listBoards()).toEqual([])
  })

  it('reindexes column positions after reorder and delete', async () => {
    const api = service()
    const board = await api.createBoard({ name: 'Cols' })
    const extra = await api.createColumn(board.id, { title: 'Review' })
    await api.updateColumn(extra.id, { position: 0 })
    const moved = await api.getBoard(board.id)
    expect(moved.columns.map((column) => column.title)).toEqual([
      'Review',
      'To Do',
      'In Progress',
      'Done',
    ])
    await api.deleteColumn(moved.columns[1].id)
    const afterDelete = await api.getBoard(board.id)
    expect(afterDelete.columns.map((column) => column.position)).toEqual([0, 1, 2])
  })

  it('creates, edits, moves, and deletes cards while reindexing', async () => {
    const api = service()
    const board = await api.createBoard({ name: 'Cards' })
    const todo = board.columns[0]
    const doing = board.columns[1]
    const first = await api.createCard(todo.id, { title: 'One', description: 'note' })
    const second = await api.createCard(todo.id, { title: 'Two' })
    expect(second.position).toBe(1)

    const edited = await api.updateCard(first.id, { title: 'One*', description: null })
    expect(edited.title).toBe('One*')
    expect(edited.description).toBeNull()

    await api.moveCard(first.id, { columnId: doing.id, position: 0 })
    const afterMove = await api.getBoard(board.id)
    expect(afterMove.columns[0].cards.map((card) => card.title)).toEqual(['Two'])
    expect(afterMove.columns[0].cards[0].position).toBe(0)
    expect(afterMove.columns[1].cards.map((card) => card.title)).toEqual(['One*'])

    await api.deleteCard(second.id)
    const afterDelete = await api.getBoard(board.id)
    expect(afterDelete.columns[0].cards).toEqual([])
  })

  it('returns structured 404s for missing records', async () => {
    const api = service()
    await expect(api.getBoard('missing')).rejects.toMatchObject({
      detail: 'Board not found',
      status: 404,
    })
    await expect(api.deleteCard('missing')).rejects.toMatchObject({
      detail: 'Card not found',
    })
  })
})
