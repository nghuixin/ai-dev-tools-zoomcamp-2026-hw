import {
  DndContext,
  PointerSensor,
  closestCorners,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import { SortableContext, horizontalListSortingStrategy } from '@dnd-kit/sortable'
import { useState, type FormEvent } from 'react'
import type { BoardDetail } from '../types'
import { ColumnLane } from './ColumnLane'

type Props = {
  board: BoardDetail
  onRenameBoard: (name: string) => Promise<void>
  onDeleteBoard: () => Promise<void>
  onCreateColumn: (title: string) => Promise<void>
  onRenameColumn: (columnId: string, title: string) => Promise<void>
  onDeleteColumn: (columnId: string) => Promise<void>
  onSetWip: (columnId: string, wipLimit: number | null) => Promise<void>
  onReorderColumn: (columnId: string, position: number) => Promise<void>
  onCreateCard: (columnId: string, title: string) => Promise<void>
  onSaveCard: (cardId: string, title: string, description: string | null) => Promise<void>
  onMoveCard: (cardId: string, columnId: string, position: number) => Promise<void>
  onDeleteCard: (cardId: string) => Promise<void>
}

function columnIdFromOver(overId: string | number | undefined, board: BoardDetail) {
  if (overId === undefined) return null
  const value = String(overId)
  if (value.startsWith('column:')) return value.slice('column:'.length)
  if (value.startsWith('lane:')) return value.slice('lane:'.length)
  const cardOwner = board.columns.find((column) =>
    column.cards.some((card) => card.id === value),
  )
  return cardOwner?.id ?? null
}

export function BoardCanvas({
  board,
  onRenameBoard,
  onDeleteBoard,
  onCreateColumn,
  onRenameColumn,
  onDeleteColumn,
  onSetWip,
  onReorderColumn,
  onCreateCard,
  onSaveCard,
  onMoveCard,
  onDeleteCard,
}: Props) {
  const [boardName, setBoardName] = useState(board.name)
  const [columnTitle, setColumnTitle] = useState('')
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
  )

  const commitBoardName = async () => {
    if (boardName.trim() && boardName !== board.name) {
      await onRenameBoard(boardName)
    } else {
      setBoardName(board.name)
    }
  }

  const addColumn = async (event: FormEvent) => {
    event.preventDefault()
    await onCreateColumn(columnTitle)
    setColumnTitle('')
  }

  const onDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event
    if (!over) return
    const activeId = String(active.id)
    if (activeId.startsWith('lane:')) {
      const columnId = activeId.slice('lane:'.length)
      const overColumnId = columnIdFromOver(over.id, board)
      if (!overColumnId || overColumnId === columnId) return
      const position = board.columns.findIndex((column) => column.id === overColumnId)
      if (position >= 0) await onReorderColumn(columnId, position)
      return
    }
    const fromColumn = board.columns.find((column) =>
      column.cards.some((card) => card.id === activeId),
    )
    const toColumnId = columnIdFromOver(over.id, board)
    if (!fromColumn || !toColumnId) return
    const toColumn = board.columns.find((column) => column.id === toColumnId)
    if (!toColumn) return
    const overId = String(over.id)
    let position = toColumn.cards.length
    const overCardIndex = toColumn.cards.findIndex((card) => card.id === overId)
    if (overCardIndex >= 0) position = overCardIndex
    await onMoveCard(activeId, toColumnId, position)
  }

  return (
    <div className="board">
      <header className="board-bar">
        <input
          className="board-name"
          aria-label="Board name"
          value={boardName}
          onChange={(event) => setBoardName(event.target.value)}
          onBlur={() => void commitBoardName()}
          maxLength={100}
        />
        <button
          type="button"
          className="ghost danger"
          onClick={() => {
            if (window.confirm(`Delete board “${board.name}”?`)) {
              void onDeleteBoard()
            }
          }}
        >
          Delete board
        </button>
      </header>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragEnd={(event) => void onDragEnd(event)}
      >
        <div className="lanes">
          <SortableContext
            items={board.columns.map((column) => `lane:${column.id}`)}
            strategy={horizontalListSortingStrategy}
          >
            {board.columns.map((column) => (
              <ColumnLane
                key={column.id}
                column={column}
                onRename={(title) => onRenameColumn(column.id, title)}
                onDelete={() => onDeleteColumn(column.id)}
                onSetWip={(wipLimit) => onSetWip(column.id, wipLimit)}
                onAddCard={(title) => onCreateCard(column.id, title)}
                onSaveCard={onSaveCard}
                onDeleteCard={onDeleteCard}
              />
            ))}
          </SortableContext>
          <form className="add-column" onSubmit={(event) => void addColumn(event)}>
            <input
              aria-label="New column title"
              placeholder="New column"
              value={columnTitle}
              onChange={(event) => setColumnTitle(event.target.value)}
              maxLength={60}
              required
            />
            <button type="submit">Add column</button>
          </form>
        </div>
      </DndContext>
    </div>
  )
}
