import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import App from './App'
import { ApiError, createMockBoardService } from './services'
import { memoryKv } from './services/storage'

function renderApp() {
  const service = createMockBoardService({ kv: memoryKv() })
  render(<App service={service} />)
  return { service, user: userEvent.setup() }
}

describe('Mini Kanban app', () => {
  it('creates a seeded board and adds a card', async () => {
    const { user } = renderApp()
    await user.type(screen.getByLabelText('New board name'), 'Sprint 1')
    await user.click(screen.getByRole('button', { name: 'Create' }))

    expect(await screen.findByLabelText('Board name')).toHaveValue('Sprint 1')
    expect(screen.getAllByLabelText('Column title').map((el) => (el as HTMLInputElement).value)).toEqual(
      ['To Do', 'In Progress', 'Done'],
    )

    await user.type(screen.getByLabelText('Add card to To Do'), 'Write spec')
    await user.click(screen.getAllByRole('button', { name: 'Add' })[0])
    expect(await screen.findByRole('heading', { name: 'Write spec' })).toBeInTheDocument()
    expect(screen.getByLabelText('1 cards')).toHaveTextContent('1')
  })

  it('edits a card inline and deletes it', async () => {
    const { user } = renderApp()
    await user.type(screen.getByLabelText('New board name'), 'Edit me')
    await user.click(screen.getByRole('button', { name: 'Create' }))
    await user.type(screen.getByLabelText('Add card to To Do'), 'Draft')
    await user.click(screen.getAllByRole('button', { name: 'Add' })[0])
    await user.click(await screen.findByRole('button', { name: 'Edit' }))
    await user.clear(screen.getByLabelText('Card title'))
    await user.type(screen.getByLabelText('Card title'), 'Ready')
    await user.type(screen.getByLabelText('Card description'), 'details')
    await user.click(screen.getByRole('button', { name: 'Save' }))
    expect(await screen.findByRole('heading', { name: 'Ready' })).toBeInTheDocument()
    expect(screen.getByText('details')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Delete card' }))
    await waitFor(() => {
      expect(screen.queryByRole('heading', { name: 'Ready' })).not.toBeInTheDocument()
    })
  })

  it('shows a service error instead of failing silently', async () => {
    const service = createMockBoardService({ kv: memoryKv() })
    service.createBoard = async () => {
      throw new ApiError('Backend unreachable', 503)
    }
    render(<App service={service} />)
    const user = userEvent.setup()
    await user.type(screen.getByLabelText('New board name'), 'Nope')
    await user.click(screen.getByRole('button', { name: 'Create' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Backend unreachable')
  })
})
