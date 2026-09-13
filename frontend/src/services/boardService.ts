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

/**
 * Single integration point for every backend call.
 * Swap the mock for an HTTP client when the FastAPI backend exists.
 */
export interface BoardService {
  listBoards(): Promise<BoardSummary[]>
  getBoard(id: string): Promise<BoardDetail>
  createBoard(input: CreateBoardInput): Promise<BoardDetail>
  updateBoard(id: string, input: UpdateBoardInput): Promise<BoardDetail>
  deleteBoard(id: string): Promise<void>
  createColumn(boardId: string, input: CreateColumnInput): Promise<Column>
  updateColumn(id: string, input: UpdateColumnInput): Promise<Column>
  deleteColumn(id: string): Promise<void>
  createCard(columnId: string, input: CreateCardInput): Promise<Card>
  updateCard(id: string, input: UpdateCardInput): Promise<Card>
  moveCard(id: string, input: MoveCardInput): Promise<Card>
  deleteCard(id: string): Promise<void>
}
