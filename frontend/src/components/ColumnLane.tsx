import { useDroppable } from '@dnd-kit/core'
import { SortableContext, useSortable, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { useState, type FormEvent } from 'react'
import type { Column } from '../types'
import { CardItem } from './CardItem'

type Props = {
  column: Column
  onRename: (title: string) => Promise<void>
  onDelete: () => Promise<void>
  onSetWip: (wipLimit: number | null) => Promise<void>
  onAddCard: (title: string) => Promise<void>
  onSaveCard: (cardId: string, title: string, description: string | null) => Promise<void>
  onDeleteCard: (cardId: string) => Promise<void>
}

export function ColumnLane({
  column,
  onRename,
  onDelete,
  onSetWip,
  onAddCard,
  onSaveCard,
  onDeleteCard,
}: Props) {
  const [title, setTitle] = useState(column.title)
  const [cardTitle, setCardTitle] = useState('')
  const [wipDraft, setWipDraft] = useState(
    column.wipLimit === null ? '' : String(column.wipLimit),
  )
  const overLimit =
    column.wipLimit !== null && column.cards.length > column.wipLimit
  const droppable = useDroppable({ id: `column:${column.id}`, data: { columnId: column.id } })
  const sortable = useSortable({ id: `lane:${column.id}`, data: { type: 'column', column } })

  const style = {
    transform: CSS.Transform.toString(sortable.transform),
    transition: sortable.transition,
  }

  const submitCard = async (event: FormEvent) => {
    event.preventDefault()
    await onAddCard(cardTitle)
    setCardTitle('')
  }

  const submitTitle = async () => {
    if (title.trim() && title !== column.title) {
      await onRename(title)
    } else {
      setTitle(column.title)
    }
  }

  const submitWip = async () => {
    if (wipDraft.trim() === '') {
      await onSetWip(null)
      return
    }
    const parsed = Number(wipDraft)
    if (Number.isInteger(parsed) && parsed >= 1) {
      await onSetWip(parsed)
    } else {
      setWipDraft(column.wipLimit === null ? '' : String(column.wipLimit))
    }
  }

  const requestDelete = async () => {
    if (column.cards.length > 0) {
      const confirmed = window.confirm(
        `Delete “${column.title}” and its ${column.cards.length} card(s)?`,
      )
      if (!confirmed) return
    }
    await onDelete()
  }

  return (
    <section
      ref={sortable.setNodeRef}
      style={style}
      className={`column ${overLimit ? 'over-wip' : ''}`}
      data-testid={`column-${column.id}`}
    >
      <header className="column-head">
        <button
          type="button"
          className="column-handle"
          aria-label={`Reorder ${column.title}`}
          {...sortable.attributes}
          {...sortable.listeners}
        >
          ::
        </button>
        <input
          className="column-title"
          aria-label="Column title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          onBlur={() => void submitTitle()}
          maxLength={60}
        />
        <span className="count" aria-label={`${column.cards.length} cards`}>
          {column.cards.length}
        </span>
        <button type="button" className="ghost danger" onClick={() => void requestDelete()}>
          Delete column
        </button>
      </header>
      <label className="wip">
        WIP
        <input
          aria-label={`WIP limit for ${column.title}`}
          inputMode="numeric"
          value={wipDraft}
          placeholder="—"
          onChange={(event) => setWipDraft(event.target.value)}
          onBlur={() => void submitWip()}
        />
      </label>
      {overLimit ? <p className="wip-warning">Over WIP limit</p> : null}
      <div ref={droppable.setNodeRef} className="card-list">
        <SortableContext
          items={column.cards.map((card) => card.id)}
          strategy={verticalListSortingStrategy}
        >
          {column.cards.map((card) => (
            <CardItem
              key={card.id}
              card={card}
              onSave={(nextTitle, description) =>
                onSaveCard(card.id, nextTitle, description)
              }
              onDelete={() => onDeleteCard(card.id)}
            />
          ))}
        </SortableContext>
      </div>
      <form className="add-card" onSubmit={(event) => void submitCard(event)}>
        <input
          aria-label={`Add card to ${column.title}`}
          placeholder="New card"
          value={cardTitle}
          onChange={(event) => setCardTitle(event.target.value)}
          maxLength={200}
          required
        />
        <button type="submit">Add</button>
      </form>
    </section>
  )
}
