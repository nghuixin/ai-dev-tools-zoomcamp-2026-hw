import { useCallback, useEffect, useState } from 'react'
import { readLastBoardId, writeLastBoardId } from './lastBoard'
import { ApiError, type BoardService } from './services'
import type { BoardDetail, BoardSummary } from './types'

function messageFrom(error: unknown) {
  if (error instanceof ApiError) return error.detail
  if (error instanceof Error) return error.message
  return 'Something went wrong'
}

export function useKanban(service: BoardService) {
  const [boards, setBoards] = useState<BoardSummary[]>([])
  const [board, setBoard] = useState<BoardDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fail = useCallback((err: unknown) => {
    setError(messageFrom(err))
  }, [])

  const refreshList = useCallback(async () => {
    const next = await service.listBoards()
    setBoards(next)
    return next
  }, [service])

  const openBoard = useCallback(
    async (boardId: string) => {
      try {
        const detail = await service.getBoard(boardId)
        setBoard(detail)
        writeLastBoardId(window.localStorage, detail.id)
        setError(null)
        return detail
      } catch (err) {
        fail(err)
      }
    },
    [fail, service],
  )

  const bootstrap = useCallback(async () => {
    setLoading(true)
    try {
      const list = await refreshList()
      const lastId = readLastBoardId(window.localStorage)
      const preferred =
        list.find((item) => item.id === lastId) ?? list[0] ?? null
      if (preferred) {
        await openBoard(preferred.id)
      } else {
        setBoard(null)
      }
      setError(null)
    } catch (err) {
      fail(err)
    } finally {
      setLoading(false)
    }
  }, [fail, openBoard, refreshList])

  useEffect(() => {
    void bootstrap()
  }, [bootstrap])

  const createBoard = useCallback(
    async (name: string) => {
      try {
        const created = await service.createBoard({ name })
        setBoard(created)
        writeLastBoardId(window.localStorage, created.id)
        await refreshList()
        setError(null)
        return created
      } catch (err) {
        fail(err)
      }
    },
    [fail, refreshList, service],
  )

  const renameBoard = useCallback(
    async (name: string) => {
      if (!board) return
      const previous = board
      setBoard({ ...board, name })
      try {
        const updated = await service.updateBoard(board.id, { name })
        setBoard(updated)
        await refreshList()
        setError(null)
      } catch (err) {
        setBoard(previous)
        fail(err)
      }
    },
    [board, fail, refreshList, service],
  )

  const deleteBoard = useCallback(async () => {
    if (!board) return
    try {
      await service.deleteBoard(board.id)
      writeLastBoardId(window.localStorage, null)
      const list = await refreshList()
      if (list[0]) await openBoard(list[0].id)
      else setBoard(null)
      setError(null)
    } catch (err) {
      fail(err)
    }
  }, [board, fail, openBoard, refreshList, service])

  const createColumn = useCallback(
    async (title: string) => {
      if (!board) return
      try {
        await service.createColumn(board.id, { title })
        setBoard(await service.getBoard(board.id))
        setError(null)
      } catch (err) {
        fail(err)
      }
    },
    [board, fail, service],
  )

  const renameColumn = useCallback(
    async (columnId: string, title: string) => {
      if (!board) return
      const previous = board
      setBoard({
        ...board,
        columns: board.columns.map((column) =>
          column.id === columnId ? { ...column, title } : column,
        ),
      })
      try {
        await service.updateColumn(columnId, { title })
        setBoard(await service.getBoard(board.id))
        setError(null)
      } catch (err) {
        setBoard(previous)
        fail(err)
      }
    },
    [board, fail, service],
  )

  const deleteColumn = useCallback(
    async (columnId: string) => {
      if (!board) return
      try {
        await service.deleteColumn(columnId)
        setBoard(await service.getBoard(board.id))
        setError(null)
      } catch (err) {
        fail(err)
      }
    },
    [board, fail, service],
  )

  const setColumnWip = useCallback(
    async (columnId: string, wipLimit: number | null) => {
      if (!board) return
      try {
        await service.updateColumn(columnId, { wipLimit })
        setBoard(await service.getBoard(board.id))
        setError(null)
      } catch (err) {
        fail(err)
      }
    },
    [board, fail, service],
  )

  const reorderColumn = useCallback(
    async (columnId: string, position: number) => {
      if (!board) return
      try {
        await service.updateColumn(columnId, { position })
        setBoard(await service.getBoard(board.id))
        setError(null)
      } catch (err) {
        fail(err)
      }
    },
    [board, fail, service],
  )

  const createCard = useCallback(
    async (columnId: string, title: string, description?: string) => {
      if (!board) return
      try {
        await service.createCard(columnId, { title, description })
        setBoard(await service.getBoard(board.id))
        setError(null)
      } catch (err) {
        fail(err)
      }
    },
    [board, fail, service],
  )

  const updateCard = useCallback(
    async (cardId: string, title: string, description: string | null) => {
      if (!board) return
      try {
        await service.updateCard(cardId, { title, description })
        setBoard(await service.getBoard(board.id))
        setError(null)
      } catch (err) {
        fail(err)
      }
    },
    [board, fail, service],
  )

  const moveCard = useCallback(
    async (cardId: string, columnId: string, position: number) => {
      if (!board) return
      const previous = board
      try {
        await service.moveCard(cardId, { columnId, position })
        setBoard(await service.getBoard(board.id))
        setError(null)
      } catch (err) {
        setBoard(previous)
        fail(err)
      }
    },
    [board, fail, service],
  )

  const deleteCard = useCallback(
    async (cardId: string) => {
      if (!board) return
      try {
        await service.deleteCard(cardId)
        setBoard(await service.getBoard(board.id))
        setError(null)
      } catch (err) {
        fail(err)
      }
    },
    [board, fail, service],
  )

  return {
    boards,
    board,
    loading,
    error,
    clearError: () => setError(null),
    openBoard,
    createBoard,
    renameBoard,
    deleteBoard,
    createColumn,
    renameColumn,
    deleteColumn,
    setColumnWip,
    reorderColumn,
    createCard,
    updateCard,
    moveCard,
    deleteCard,
  }
}
