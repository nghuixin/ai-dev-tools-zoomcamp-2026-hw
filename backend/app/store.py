from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from app.errors import StoreError
from app.models import (
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
)

DEFAULT_COLUMN_TITLES = ("To Do", "In Progress", "Done")


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class StoredBoard:
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


@dataclass
class StoredColumn:
    id: UUID
    board_id: UUID
    title: str
    position: int
    wip_limit: Optional[int]


@dataclass
class StoredCard:
    id: UUID
    column_id: UUID
    title: str
    description: Optional[str]
    position: int
    created_at: datetime
    updated_at: datetime


@dataclass
class Store:
    boards: dict[UUID, StoredBoard] = field(default_factory=dict)
    columns: dict[UUID, StoredColumn] = field(default_factory=dict)
    cards: dict[UUID, StoredCard] = field(default_factory=dict)

    def reset(self) -> None:
        self.boards.clear()
        self.columns.clear()
        self.cards.clear()

    def seed(self) -> BoardDetail:
        board = self.create_board(CreateBoardInput(name="Workshop"))
        todo = board.columns[0]
        doing = board.columns[1]
        self.create_card(todo.id, CreateCardInput(title="Write OpenAPI contract"))
        self.create_card(
            todo.id,
            CreateCardInput(title="Connect frontend", description="Swap mock for HTTP client"),
        )
        self.create_card(doing.id, CreateCardInput(title="Review in-memory store"))
        return self.get_board(board.id)

    def _require_board(self, board_id: UUID) -> StoredBoard:
        board = self.boards.get(board_id)
        if not board:
            raise StoreError("Board not found", 404)
        return board

    def _require_column(self, column_id: UUID) -> StoredColumn:
        column = self.columns.get(column_id)
        if not column:
            raise StoreError("Column not found", 404)
        return column

    def _require_card(self, card_id: UUID) -> StoredCard:
        card = self.cards.get(card_id)
        if not card:
            raise StoreError("Card not found", 404)
        return card

    def _touch(self, board: StoredBoard) -> None:
        board.updated_at = _now()

    def _board_columns(self, board_id: UUID) -> list[StoredColumn]:
        columns = [c for c in self.columns.values() if c.board_id == board_id]
        columns.sort(key=lambda c: c.position)
        for index, column in enumerate(columns):
            column.position = index
        return columns

    def _column_cards(self, column_id: UUID) -> list[StoredCard]:
        cards = [c for c in self.cards.values() if c.column_id == column_id]
        cards.sort(key=lambda c: c.position)
        for index, card in enumerate(cards):
            card.position = index
        return cards

    def _card_out(self, card: StoredCard) -> Card:
        return Card(
            id=card.id,
            columnId=card.column_id,
            title=card.title,
            description=card.description,
            position=card.position,
            createdAt=card.created_at,
            updatedAt=card.updated_at,
        )

    def _column_out(self, column: StoredColumn) -> Column:
        return Column(
            id=column.id,
            boardId=column.board_id,
            title=column.title,
            position=column.position,
            wipLimit=column.wip_limit,
            cards=[self._card_out(card) for card in self._column_cards(column.id)],
        )

    def _board_out(self, board: StoredBoard) -> BoardDetail:
        return BoardDetail(
            id=board.id,
            name=board.name,
            createdAt=board.created_at,
            updatedAt=board.updated_at,
            columns=[self._column_out(column) for column in self._board_columns(board.id)],
        )

    def list_boards(self) -> list[BoardSummary]:
        boards = sorted(self.boards.values(), key=lambda b: b.updated_at, reverse=True)
        return [
            BoardSummary(
                id=board.id,
                name=board.name,
                createdAt=board.created_at,
                updatedAt=board.updated_at,
            )
            for board in boards
        ]

    def get_board(self, board_id: UUID) -> BoardDetail:
        return self._board_out(self._require_board(board_id))

    def create_board(self, data: CreateBoardInput) -> BoardDetail:
        timestamp = _now()
        board = StoredBoard(
            id=uuid4(),
            name=data.name,
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.boards[board.id] = board
        for position, title in enumerate(DEFAULT_COLUMN_TITLES):
            column = StoredColumn(
                id=uuid4(),
                board_id=board.id,
                title=title,
                position=position,
                wip_limit=None,
            )
            self.columns[column.id] = column
        return self._board_out(board)

    def update_board(self, board_id: UUID, data: UpdateBoardInput) -> BoardDetail:
        board = self._require_board(board_id)
        board.name = data.name
        self._touch(board)
        return self._board_out(board)

    def delete_board(self, board_id: UUID) -> None:
        self._require_board(board_id)
        column_ids = [cid for cid, col in self.columns.items() if col.board_id == board_id]
        for card_id, card in list(self.cards.items()):
            if card.column_id in column_ids:
                del self.cards[card_id]
        for column_id in column_ids:
            del self.columns[column_id]
        del self.boards[board_id]

    def create_column(self, board_id: UUID, data: CreateColumnInput) -> Column:
        board = self._require_board(board_id)
        siblings = self._board_columns(board_id)
        column = StoredColumn(
            id=uuid4(),
            board_id=board_id,
            title=data.title,
            position=len(siblings),
            wip_limit=data.wipLimit,
        )
        self.columns[column.id] = column
        self._touch(board)
        return self._column_out(column)

    def update_column(self, column_id: UUID, data: UpdateColumnInput) -> Column:
        if not data.model_fields_set:
            raise StoreError("At least one field is required")
        column = self._require_column(column_id)
        board = self._require_board(column.board_id)
        if data.title is not None:
            column.title = data.title
        if "wipLimit" in data.model_fields_set:
            column.wip_limit = data.wipLimit
        if data.position is not None:
            siblings = self._board_columns(column.board_id)
            siblings = [item for item in siblings if item.id != column.id]
            insert_at = min(data.position, len(siblings))
            siblings.insert(insert_at, column)
            for index, item in enumerate(siblings):
                item.position = index
        self._touch(board)
        return self._column_out(column)

    def delete_column(self, column_id: UUID) -> None:
        column = self._require_column(column_id)
        board = self._require_board(column.board_id)
        for card_id, card in list(self.cards.items()):
            if card.column_id == column_id:
                del self.cards[card_id]
        del self.columns[column_id]
        self._board_columns(board.id)
        self._touch(board)

    def create_card(self, column_id: UUID, data: CreateCardInput) -> Card:
        column = self._require_column(column_id)
        board = self._require_board(column.board_id)
        siblings = self._column_cards(column_id)
        timestamp = _now()
        card = StoredCard(
            id=uuid4(),
            column_id=column_id,
            title=data.title,
            description=data.description,
            position=len(siblings),
            created_at=timestamp,
            updated_at=timestamp,
        )
        self.cards[card.id] = card
        self._touch(board)
        return self._card_out(card)

    def update_card(self, card_id: UUID, data: UpdateCardInput) -> Card:
        if not data.model_fields_set:
            raise StoreError("At least one field is required")
        card = self._require_card(card_id)
        column = self._require_column(card.column_id)
        board = self._require_board(column.board_id)
        if data.title is not None:
            card.title = data.title
        if "description" in data.model_fields_set:
            card.description = data.description
        card.updated_at = _now()
        self._touch(board)
        return self._card_out(card)

    def move_card(self, card_id: UUID, data: MoveCardInput) -> Card:
        card = self._require_card(card_id)
        source = self._require_column(card.column_id)
        target = self._require_column(data.columnId)
        if source.board_id != target.board_id:
            raise StoreError("Cannot move a card to another board")
        card.column_id = target.id
        self._column_cards(source.id)
        targets = [item for item in self._column_cards(target.id) if item.id != card.id]
        insert_at = min(data.position, len(targets))
        targets.insert(insert_at, card)
        for index, item in enumerate(targets):
            item.position = index
        card.updated_at = _now()
        self._touch(self._require_board(target.board_id))
        return self._card_out(card)

    def delete_card(self, card_id: UUID) -> None:
        card = self._require_card(card_id)
        column = self._require_column(card.column_id)
        board = self._require_board(column.board_id)
        del self.cards[card_id]
        self._column_cards(column.id)
        self._touch(board)
