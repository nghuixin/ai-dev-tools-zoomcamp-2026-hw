import type { BoardService } from './boardService'
import { createHttpBoardService } from './httpBoardService'

export type { BoardService } from './boardService'
export { ApiError } from './errors'
export { createHttpBoardService } from './httpBoardService'
export { createMockBoardService } from './mockBoardService'

/** Live FastAPI client. Tests can still inject createMockBoardService(). */
export const boardService: BoardService = createHttpBoardService()
