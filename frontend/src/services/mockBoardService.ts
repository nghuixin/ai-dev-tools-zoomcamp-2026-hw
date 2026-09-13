import type {
  BoardDetail,
  BoardSummary,
  Card,
  Column,
  CreateBoardInput,
  CreateCardInput,
  CreateColumnInput,
  MoveCardInput,
  UpdateBoardInput,
  UpdateCardInput,
  UpdateColumnInput,
} from '../types'
import type { BoardService } from './boardService'
import { ApiError } from './errors'
import { browserKv, type KvStore } from './storage'

const STORE_KEY = 'mini-kanban.mock.v1'
export const DEFAULT_COLUMN_TITLES = ['To Do', 'In Progress', 'Done'] as const

type StoredBoard = Omit<BoardSummary, never>
type StoredColumn = Omit<Column, 'cards'>
type StoredCard = Card

type Snapshot = {
  boards: StoredBoard[]
  columns: StoredColumn[]
  cards: StoredCard[]
}

export type MockBoardServiceOptions = {
  kv?: KvStore
  now?: () => string
  id?: () => string
}

function emptySnapshot(): Snapshot {
  return { boards: [], columns: [], cards: [] }
}

function requireLength(value: string, field: string, min: number, max: number) {
  const trimmed = value.trim()
  if (trimmed.length < min || trimmed.length > max) {
    throw new ApiError(`${field} must be ${min}–${max} characters`)
  }
  return trimmed
}

function reindex<T extends { position: number }>(items: T[]): T[] {
  return items
    .slice()
    .sort((a, b) => a.position - b.position)
    .map((item, position) => ({ ...item, position }))
}

export function createMockBoardService(
  options: MockBoardServiceOptions = {},
): BoardService {
  const kv = options.kv ?? browserKv()
  const now = options.now ?? (() => new Date().toISOString())
  const id = options.id ?? (() => crypto.randomUUID())

  const load = (): Snapshot => {
    const raw = kv.getItem(STORE_KEY)
    if (!raw) return emptySnapshot()
    try {
      return JSON.parse(raw) as Snapshot
    } catch {
      return emptySnapshot()
    }
  }

  const save = (snapshot: Snapshot) => {
    kv.setItem(STORE_KEY, JSON.stringify(snapshot))
  }

  const nestBoard = (snapshot: Snapshot, board: StoredBoard): BoardDetail => {
    const columns = reindex(
      snapshot.columns.filter((column) => column.boardId === board.id),
    ).map((column) => ({
      ...column,
      cards: reindex(
        snapshot.cards.filter((card) => card.columnId === column.id),
      ),
    }))
    return { ...board, columns }
  }

  const requireBoard = (snapshot: Snapshot, boardId: string) => {
    const board = snapshot.boards.find((item) => item.id === boardId)
    if (!board) throw new ApiError('Board not found', 404)
    return board
  }

  const requireColumn = (snapshot: Snapshot, columnId: string) => {
    const column = snapshot.columns.find((item) => item.id === columnId)
    if (!column) throw new ApiError('Column not found', 404)
    return column
  }

  const requireCard = (snapshot: Snapshot, cardId: string) => {
    const card = snapshot.cards.find((item) => item.id === cardId)
    if (!card) throw new ApiError('Card not found', 404)
    return card
  }

  return {
    async listBoards() {
      return load()
        .boards.slice()
        .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
    },

    async getBoard(boardId) {
      const snapshot = load()
      return nestBoard(snapshot, requireBoard(snapshot, boardId))
    },

    async createBoard(input: CreateBoardInput) {
      const name = requireLength(input.name, 'Board name', 1, 100)
      const snapshot = load()
      const timestamp = now()
      const board: StoredBoard = {
        id: id(),
        name,
        createdAt: timestamp,
        updatedAt: timestamp,
      }
      snapshot.boards.push(board)
      DEFAULT_COLUMN_TITLES.forEach((title, position) => {
        snapshot.columns.push({
          id: id(),
          boardId: board.id,
          title,
          position,
          wipLimit: null,
        })
      })
      save(snapshot)
      return nestBoard(snapshot, board)
    },

    async updateBoard(boardId, input: UpdateBoardInput) {
      const name = requireLength(input.name, 'Board name', 1, 100)
      const snapshot = load()
      const board = requireBoard(snapshot, boardId)
      board.name = name
      board.updatedAt = now()
      save(snapshot)
      return nestBoard(snapshot, board)
    },

    async deleteBoard(boardId) {
      const snapshot = load()
      requireBoard(snapshot, boardId)
      const columnIds = new Set(
        snapshot.columns
          .filter((column) => column.boardId === boardId)
          .map((column) => column.id),
      )
      snapshot.boards = snapshot.boards.filter((board) => board.id !== boardId)
      snapshot.columns = snapshot.columns.filter(
        (column) => column.boardId !== boardId,
      )
      snapshot.cards = snapshot.cards.filter(
        (card) => !columnIds.has(card.columnId),
      )
      save(snapshot)
    },

    async createColumn(boardId, input: CreateColumnInput) {
      const title = requireLength(input.title, 'Column title', 1, 60)
      const snapshot = load()
      const board = requireBoard(snapshot, boardId)
      const siblings = snapshot.columns.filter(
        (column) => column.boardId === boardId,
      )
      const column: StoredColumn = {
        id: id(),
        boardId,
        title,
        position: siblings.length,
        wipLimit: input.wipLimit ?? null,
      }
      snapshot.columns.push(column)
      board.updatedAt = now()
      save(snapshot)
      return { ...column, cards: [] }
    },

    async updateColumn(columnId, input: UpdateColumnInput) {
      const snapshot = load()
      const column = requireColumn(snapshot, columnId)
      const board = requireBoard(snapshot, column.boardId)
      if (input.title !== undefined) {
        column.title = requireLength(input.title, 'Column title', 1, 60)
      }
      if (input.wipLimit !== undefined) {
        if (input.wipLimit !== null && input.wipLimit < 1) {
          throw new ApiError('WIP limit must be at least 1')
        }
        column.wipLimit = input.wipLimit
      }
      if (input.position !== undefined) {
        const siblings = snapshot.columns
          .filter((item) => item.boardId === column.boardId)
          .sort((a, b) => a.position - b.position)
        const from = siblings.findIndex((item) => item.id === column.id)
        const to = Math.max(0, Math.min(input.position, siblings.length - 1))
        const [moved] = siblings.splice(from, 1)
        siblings.splice(to, 0, moved)
        siblings.forEach((item, position) => {
          item.position = position
        })
      }
      board.updatedAt = now()
      save(snapshot)
      return {
        ...column,
        cards: reindex(
          snapshot.cards.filter((card) => card.columnId === column.id),
        ),
      }
    },

    async deleteColumn(columnId) {
      const snapshot = load()
      const column = requireColumn(snapshot, columnId)
      const board = requireBoard(snapshot, column.boardId)
      snapshot.columns = snapshot.columns.filter((item) => item.id !== columnId)
      snapshot.cards = snapshot.cards.filter(
        (card) => card.columnId !== columnId,
      )
      const remaining = reindex(
        snapshot.columns.filter((item) => item.boardId === column.boardId),
      )
      snapshot.columns = snapshot.columns
        .filter((item) => item.boardId !== column.boardId)
        .concat(remaining)
      board.updatedAt = now()
      save(snapshot)
    },

    async createCard(columnId, input: CreateCardInput) {
      const title = requireLength(input.title, 'Card title', 1, 200)
      let description: string | null = null
      if (input.description) {
        description = requireLength(input.description, 'Description', 1, 2000)
      }
      const snapshot = load()
      const column = requireColumn(snapshot, columnId)
      const board = requireBoard(snapshot, column.boardId)
      const siblings = snapshot.cards.filter((card) => card.columnId === columnId)
      const card: StoredCard = {
        id: id(),
        columnId,
        title,
        description,
        position: siblings.length,
        createdAt: now(),
        updatedAt: now(),
      }
      snapshot.cards.push(card)
      board.updatedAt = now()
      save(snapshot)
      return card
    },

    async updateCard(cardId, input: UpdateCardInput) {
      const snapshot = load()
      const card = requireCard(snapshot, cardId)
      const column = requireColumn(snapshot, card.columnId)
      const board = requireBoard(snapshot, column.boardId)
      if (input.title !== undefined) {
        card.title = requireLength(input.title, 'Card title', 1, 200)
      }
      if (input.description !== undefined) {
        if (input.description === null || input.description.trim() === '') {
          card.description = null
        } else {
          card.description = requireLength(
            input.description,
            'Description',
            1,
            2000,
          )
        }
      }
      card.updatedAt = now()
      board.updatedAt = now()
      save(snapshot)
      return card
    },

    async moveCard(cardId, input: MoveCardInput) {
      const snapshot = load()
      const card = requireCard(snapshot, cardId)
      const sourceColumn = requireColumn(snapshot, card.columnId)
      const targetColumn = requireColumn(snapshot, input.columnId)
      if (sourceColumn.boardId !== targetColumn.boardId) {
        throw new ApiError('Cannot move a card to another board')
      }
      const sourceCards = snapshot.cards
        .filter((item) => item.columnId === card.columnId && item.id !== card.id)
        .sort((a, b) => a.position - b.position)
      sourceCards.forEach((item, position) => {
        item.position = position
      })

      card.columnId = targetColumn.id
      const targetCards = snapshot.cards
        .filter((item) => item.columnId === targetColumn.id && item.id !== card.id)
        .sort((a, b) => a.position - b.position)
      const insertAt = Math.max(0, Math.min(input.position, targetCards.length))
      targetCards.splice(insertAt, 0, card)
      targetCards.forEach((item, position) => {
        item.position = position
      })
      card.updatedAt = now()
      requireBoard(snapshot, targetColumn.boardId).updatedAt = now()
      save(snapshot)
      return card
    },

    async deleteCard(cardId) {
      const snapshot = load()
      const card = requireCard(snapshot, cardId)
      const column = requireColumn(snapshot, card.columnId)
      const board = requireBoard(snapshot, column.boardId)
      snapshot.cards = snapshot.cards.filter((item) => item.id !== cardId)
      const remaining = reindex(
        snapshot.cards.filter((item) => item.columnId === column.id),
      )
      snapshot.cards = snapshot.cards
        .filter((item) => item.columnId !== column.id)
        .concat(remaining)
      board.updatedAt = now()
      save(snapshot)
    },
  }
}
