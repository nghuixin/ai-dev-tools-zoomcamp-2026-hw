export type BoardSummary = {
  id: string
  name: string
  createdAt: string
  updatedAt: string
}

export type Card = {
  id: string
  columnId: string
  title: string
  description: string | null
  position: number
  createdAt: string
  updatedAt: string
}

export type Column = {
  id: string
  boardId: string
  title: string
  position: number
  wipLimit: number | null
  cards: Card[]
}

export type BoardDetail = BoardSummary & {
  columns: Column[]
}

export type CreateBoardInput = { name: string }
export type UpdateBoardInput = { name: string }
export type CreateColumnInput = { title: string; wipLimit?: number | null }
export type UpdateColumnInput = {
  title?: string
  wipLimit?: number | null
  position?: number
}
export type CreateCardInput = { title: string; description?: string | null }
export type UpdateCardInput = { title?: string; description?: string | null }
export type MoveCardInput = { columnId: string; position: number }
