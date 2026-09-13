import { useState, type FormEvent } from 'react'
import { BoardCanvas } from './components/BoardCanvas'
import { boardService, type BoardService } from './services'
import { useKanban } from './useKanban'

type Props = {
  service?: BoardService
}

export default function App({ service = boardService }: Props) {
  const kanban = useKanban(service)
  const [newBoardName, setNewBoardName] = useState('')

  const createBoard = async (event: FormEvent) => {
    event.preventDefault()
    await kanban.createBoard(newBoardName)
    setNewBoardName('')
  }

  return (
    <div className="app">
      <header className="topbar">
        <p className="brand">Mini Kanban</p>
        {kanban.boards.length > 0 ? (
          <label className="board-switch">
            Board
            <select
              aria-label="Open board"
              value={kanban.board?.id ?? ''}
              onChange={(event) => void kanban.openBoard(event.target.value)}
            >
              {kanban.boards.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
        ) : null}
        <form className="create-board" onSubmit={(event) => void createBoard(event)}>
          <input
            aria-label="New board name"
            placeholder="New board"
            value={newBoardName}
            onChange={(event) => setNewBoardName(event.target.value)}
            maxLength={100}
            required
          />
          <button type="submit">Create</button>
        </form>
      </header>

      {kanban.error ? (
        <div className="banner" role="alert">
          <span>{kanban.error}</span>
          <button type="button" className="ghost" onClick={kanban.clearError}>
            Dismiss
          </button>
        </div>
      ) : null}

      {kanban.loading ? <p className="status">Loading board…</p> : null}

      {!kanban.loading && !kanban.board ? (
        <main className="welcome">
          <h1>A board in under 30 seconds</h1>
          <p>Name it, get To Do / In Progress / Done, start dragging cards. No account.</p>
        </main>
      ) : null}

      {kanban.board ? (
        <BoardCanvas
          key={kanban.board.id}
          board={kanban.board}
          onRenameBoard={kanban.renameBoard}
          onDeleteBoard={kanban.deleteBoard}
          onCreateColumn={kanban.createColumn}
          onRenameColumn={kanban.renameColumn}
          onDeleteColumn={kanban.deleteColumn}
          onSetWip={kanban.setColumnWip}
          onReorderColumn={kanban.reorderColumn}
          onCreateCard={kanban.createCard}
          onSaveCard={kanban.updateCard}
          onMoveCard={kanban.moveCard}
          onDeleteCard={kanban.deleteCard}
        />
      ) : null}
    </div>
  )
}
