from uuid import uuid4

import pytest

from app.errors import StoreError
from app.models import (
    CreateBoardInput,
    CreateCardInput,
    CreateColumnInput,
    MoveCardInput,
    UpdateCardInput,
    UpdateColumnInput,
)
from app.store import DEFAULT_COLUMN_TITLES, Store


def test_seed_creates_workshop_with_default_columns_and_cards():
    store = Store()
    board = store.seed()
    assert board.name == "Workshop"
    assert [column.title for column in board.columns] == list(DEFAULT_COLUMN_TITLES)
    assert [card.title for card in board.columns[0].cards] == [
        "Write OpenAPI contract",
        "Connect frontend",
    ]
    assert store.list_boards()[0].id == board.id


def test_delete_board_cascades_columns_and_cards():
    store = Store()
    board = store.create_board(CreateBoardInput(name="Temp"))
    store.create_card(board.columns[0].id, CreateCardInput(title="Task"))
    store.delete_board(board.id)
    with pytest.raises(StoreError) as exc:
        store.get_board(board.id)
    assert exc.value.status == 404
    assert store.list_boards() == []


def test_column_reorder_and_delete_reindexes():
    store = Store()
    board = store.create_board(CreateBoardInput(name="Cols"))
    extra = store.create_column(board.id, CreateColumnInput(title="Review"))
    store.update_column(extra.id, UpdateColumnInput(position=0))
    titles = [column.title for column in store.get_board(board.id).columns]
    assert titles == ["Review", "To Do", "In Progress", "Done"]
    store.delete_column(store.get_board(board.id).columns[1].id)
    positions = [column.position for column in store.get_board(board.id).columns]
    assert positions == [0, 1, 2]


def test_move_card_reindexes_source_and_target():
    store = Store()
    board = store.create_board(CreateBoardInput(name="Cards"))
    todo, doing = board.columns[0], board.columns[1]
    first = store.create_card(todo.id, CreateCardInput(title="One"))
    store.create_card(todo.id, CreateCardInput(title="Two"))
    store.move_card(first.id, MoveCardInput(columnId=doing.id, position=0))
    after = store.get_board(board.id)
    assert [card.title for card in after.columns[0].cards] == ["Two"]
    assert after.columns[0].cards[0].position == 0
    assert [card.title for card in after.columns[1].cards] == ["One"]


def test_update_card_can_clear_description():
    store = Store()
    board = store.create_board(CreateBoardInput(name="Edit"))
    card = store.create_card(
        board.columns[0].id,
        CreateCardInput(title="Note", description="keep"),
    )
    updated = store.update_card(card.id, UpdateCardInput(description=None))
    assert updated.description is None


def test_unknown_ids_are_404():
    store = Store()
    missing = uuid4()
    with pytest.raises(StoreError) as board_exc:
        store.get_board(missing)
    with pytest.raises(StoreError) as card_exc:
        store.delete_card(missing)
    assert board_exc.value.detail == "Board not found"
    assert card_exc.value.detail == "Card not found"


def test_cannot_move_across_boards():
    store = Store()
    first = store.create_board(CreateBoardInput(name="A"))
    second = store.create_board(CreateBoardInput(name="B"))
    card = store.create_card(first.columns[0].id, CreateCardInput(title="X"))
    with pytest.raises(StoreError) as exc:
        store.move_card(
            card.id,
            MoveCardInput(columnId=second.columns[0].id, position=0),
        )
    assert exc.value.status == 400
    assert exc.value.detail == "Cannot move a card to another board"
