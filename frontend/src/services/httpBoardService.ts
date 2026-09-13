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

export const DEFAULT_API_URL = 'http://localhost:8091'

export type HttpBoardServiceOptions = {
  baseUrl?: string
  fetchImpl?: typeof fetch
}

function apiBaseUrl() {
  const fromEnv = import.meta.env.VITE_API_URL
  return typeof fromEnv === 'string' && fromEnv.length > 0 ? fromEnv : DEFAULT_API_URL
}

async function parseBody(response: Response): Promise<unknown> {
  if (response.status === 204) return undefined
  const text = await response.text()
  if (!text) return undefined
  try {
    return JSON.parse(text)
  } catch {
    return { detail: text }
  }
}

function detailFrom(body: unknown, fallback: string) {
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
  }
  return fallback
}

export function createHttpBoardService(
  options: HttpBoardServiceOptions = {},
): BoardService {
  const baseUrl = (options.baseUrl ?? apiBaseUrl()).replace(/\/$/, '')
  const fetchImpl = options.fetchImpl ?? fetch

  async function request<T>(path: string, init?: RequestInit): Promise<T> {
    let response: Response
    try {
      response = await fetchImpl(`${baseUrl}${path}`, {
        ...init,
        headers: {
          Accept: 'application/json',
          ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
          ...init?.headers,
        },
      })
    } catch {
      throw new ApiError('Backend unreachable', 503)
    }

    const body = await parseBody(response)
    if (!response.ok) {
      throw new ApiError(detailFrom(body, response.statusText), response.status)
    }
    return body as T
  }

  return {
    listBoards: () => request<BoardSummary[]>('/boards'),
    getBoard: (id) => request<BoardDetail>(`/boards/${id}`),
    createBoard: (input: CreateBoardInput) =>
      request<BoardDetail>('/boards', {
        method: 'POST',
        body: JSON.stringify(input),
      }),
    updateBoard: (id, input: UpdateBoardInput) =>
      request<BoardDetail>(`/boards/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(input),
      }),
    deleteBoard: async (id) => {
      await request<void>(`/boards/${id}`, { method: 'DELETE' })
    },
    createColumn: (boardId, input: CreateColumnInput) =>
      request<Column>(`/boards/${boardId}/columns`, {
        method: 'POST',
        body: JSON.stringify(input),
      }),
    updateColumn: (id, input: UpdateColumnInput) =>
      request<Column>(`/columns/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(input),
      }),
    deleteColumn: async (id) => {
      await request<void>(`/columns/${id}`, { method: 'DELETE' })
    },
    createCard: (columnId, input: CreateCardInput) =>
      request<Card>(`/columns/${columnId}/cards`, {
        method: 'POST',
        body: JSON.stringify(input),
      }),
    updateCard: (id, input: UpdateCardInput) =>
      request<Card>(`/cards/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(input),
      }),
    moveCard: (id, input: MoveCardInput) =>
      request<Card>(`/cards/${id}/move`, {
        method: 'POST',
        body: JSON.stringify(input),
      }),
    deleteCard: async (id) => {
      await request<void>(`/cards/${id}`, { method: 'DELETE' })
    },
  }
}
