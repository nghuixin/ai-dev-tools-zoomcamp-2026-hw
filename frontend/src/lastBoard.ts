const LAST_BOARD_KEY = 'mini-kanban.lastBoardId'

export function readLastBoardId(kv: Pick<Storage, 'getItem'> | undefined) {
  if (!kv) return null
  return kv.getItem(LAST_BOARD_KEY)
}

export function writeLastBoardId(
  kv: Pick<Storage, 'setItem' | 'removeItem'> | undefined,
  boardId: string | null,
) {
  if (!kv) return
  if (boardId) kv.setItem(LAST_BOARD_KEY, boardId)
  else kv.removeItem(LAST_BOARD_KEY)
}
