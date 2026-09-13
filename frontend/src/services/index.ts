import type { BoardService } from './boardService'
import { createMockBoardService } from './mockBoardService'

export type { BoardService } from './boardService'
export { ApiError } from './errors'
export { createMockBoardService } from './mockBoardService'

/** Active backend client. Replace this export when wiring FastAPI. */
export const boardService: BoardService = createMockBoardService()
