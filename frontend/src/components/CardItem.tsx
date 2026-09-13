import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { useState, type FormEvent } from 'react'
import type { Card } from '../types'

type Props = {
  card: Card
  onSave: (title: string, description: string | null) => Promise<void>
  onDelete: () => Promise<void>
}

export function CardItem({ card, onSave, onDelete }: Props) {
  const [editing, setEditing] = useState(false)
  const [title, setTitle] = useState(card.title)
  const [description, setDescription] = useState(card.description ?? '')
  const sortable = useSortable({ id: card.id, data: { type: 'card', card } })

  const style = {
    transform: CSS.Transform.toString(sortable.transform),
    transition: sortable.transition,
    opacity: sortable.isDragging ? 0.45 : 1,
  }

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    await onSave(title, description.trim() === '' ? null : description)
    setEditing(false)
  }

  return (
    <article
      ref={sortable.setNodeRef}
      style={style}
      className="card"
      data-testid={`card-${card.id}`}
    >
      <button
        type="button"
        className="card-handle"
        aria-label={`Drag ${card.title}`}
        {...sortable.attributes}
        {...sortable.listeners}
      >
        ::
      </button>
      {editing ? (
        <form className="card-edit" onSubmit={(event) => void submit(event)}>
          <input
            aria-label="Card title"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            maxLength={200}
            required
          />
          <textarea
            aria-label="Card description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            maxLength={2000}
            rows={3}
            placeholder="Optional description"
          />
          <div className="row">
            <button type="submit">Save</button>
            <button type="button" className="ghost" onClick={() => setEditing(false)}>
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <div className="card-body">
          <h3>{card.title}</h3>
          {card.description ? <p>{card.description}</p> : null}
          <div className="row">
            <button type="button" className="ghost" onClick={() => setEditing(true)}>
              Edit
            </button>
            <button type="button" className="ghost danger" onClick={() => void onDelete()}>
              Delete card
            </button>
          </div>
        </div>
      )}
    </article>
  )
}
