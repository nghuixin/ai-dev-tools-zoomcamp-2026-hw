from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.database import create_memory_session_factory
from app.db_models import BoardRow, CardRow, ColumnRow
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


class Store:
    def __init__(self, session_factory: sessionmaker | None = None) -> None:
        self._session_factory = session_factory or create_memory_session_factory()

    @contextmanager
    def _session(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

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

    def _require_board(self, session: Session, board_id: UUID) -> BoardRow:
        board = session.get(BoardRow, board_id)
        if not board:
            raise StoreError("Board not found", 404)
        return board

    def _require_column(self, session: Session, column_id: UUID) -> ColumnRow:
        column = session.get(ColumnRow, column_id)
        if not column:
            raise StoreError("Column not found", 404)
        return column

    def _require_card(self, session: Session, card_id: UUID) -> CardRow:
        card = session.get(CardRow, card_id)
        if not card:
            raise StoreError("Card not found", 404)
        return card

    def _touch(self, board: BoardRow) -> None:
        board.updated_at = _now()

    def _board_columns(self, session: Session, board_id: UUID) -> list[ColumnRow]:
        columns = list(
            session.scalars(
                select(ColumnRow)
                .where(ColumnRow.board_id == board_id)
                .order_by(ColumnRow.position, ColumnRow.id)
            )
        )
        for index, column in enumerate(columns):
            column.position = index
        return columns

    def _column_cards(self, session: Session, column_id: UUID) -> list[CardRow]:
        cards = list(
            session.scalars(
                select(CardRow)
                .where(CardRow.column_id == column_id)
                .order_by(CardRow.position, CardRow.id)
            )
        )
        for index, card in enumerate(cards):
            card.position = index
        return cards

    def _card_out(self, card: CardRow) -> Card:
        return Card(
            id=card.id,
            columnId=card.column_id,
            title=card.title,
            description=card.description,
            position=card.position,
            createdAt=card.created_at,
            updatedAt=card.updated_at,
        )

    def _column_out(self, session: Session, column: ColumnRow) -> Column:
        return Column(
            id=column.id,
            boardId=column.board_id,
            title=column.title,
            position=column.position,
            wipLimit=column.wip_limit,
            cards=[self._card_out(card) for card in self._column_cards(session, column.id)],
        )

    def _board_out(self, session: Session, board: BoardRow) -> BoardDetail:
        return BoardDetail(
            id=board.id,
            name=board.name,
            createdAt=board.created_at,
            updatedAt=board.updated_at,
            columns=[
                self._column_out(session, column)
                for column in self._board_columns(session, board.id)
            ],
        )

    def list_boards(self) -> list[BoardSummary]:
        with self._session() as session:
            boards = list(
                session.scalars(select(BoardRow).order_by(BoardRow.updated_at.desc()))
            )
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
        with self._session() as session:
            return self._board_out(session, self._require_board(session, board_id))

    def create_board(self, data: CreateBoardInput) -> BoardDetail:
        timestamp = _now()
        with self._session() as session:
            board = BoardRow(
                id=uuid4(),
                name=data.name,
                created_at=timestamp,
                updated_at=timestamp,
            )
            session.add(board)
            for position, title in enumerate(DEFAULT_COLUMN_TITLES):
                session.add(
                    ColumnRow(
                        id=uuid4(),
                        board_id=board.id,
                        title=title,
                        position=position,
                        wip_limit=None,
                    )
                )
            session.flush()
            return self._board_out(session, board)

    def update_board(self, board_id: UUID, data: UpdateBoardInput) -> BoardDetail:
        with self._session() as session:
            board = self._require_board(session, board_id)
            board.name = data.name
            self._touch(board)
            return self._board_out(session, board)

    def delete_board(self, board_id: UUID) -> None:
        with self._session() as session:
            board = self._require_board(session, board_id)
            session.delete(board)

    def create_column(self, board_id: UUID, data: CreateColumnInput) -> Column:
        with self._session() as session:
            board = self._require_board(session, board_id)
            siblings = self._board_columns(session, board_id)
            column = ColumnRow(
                id=uuid4(),
                board_id=board_id,
                title=data.title,
                position=len(siblings),
                wip_limit=data.wipLimit,
            )
            session.add(column)
            self._touch(board)
            session.flush()
            return self._column_out(session, column)

    def update_column(self, column_id: UUID, data: UpdateColumnInput) -> Column:
        if not data.model_fields_set:
            raise StoreError("At least one field is required")
        with self._session() as session:
            column = self._require_column(session, column_id)
            board = self._require_board(session, column.board_id)
            if data.title is not None:
                column.title = data.title
            if "wipLimit" in data.model_fields_set:
                column.wip_limit = data.wipLimit
            if data.position is not None:
                siblings = [
                    item
                    for item in self._board_columns(session, column.board_id)
                    if item.id != column.id
                ]
                insert_at = min(data.position, len(siblings))
                siblings.insert(insert_at, column)
                for index, item in enumerate(siblings):
                    item.position = index
            self._touch(board)
            return self._column_out(session, column)

    def delete_column(self, column_id: UUID) -> None:
        with self._session() as session:
            column = self._require_column(session, column_id)
            board = self._require_board(session, column.board_id)
            session.delete(column)
            session.flush()
            self._board_columns(session, board.id)
            self._touch(board)

    def create_card(self, column_id: UUID, data: CreateCardInput) -> Card:
        with self._session() as session:
            column = self._require_column(session, column_id)
            board = self._require_board(session, column.board_id)
            siblings = self._column_cards(session, column_id)
            timestamp = _now()
            card = CardRow(
                id=uuid4(),
                column_id=column_id,
                title=data.title,
                description=data.description,
                position=len(siblings),
                created_at=timestamp,
                updated_at=timestamp,
            )
            session.add(card)
            self._touch(board)
            session.flush()
            return self._card_out(card)

    def update_card(self, card_id: UUID, data: UpdateCardInput) -> Card:
        if not data.model_fields_set:
            raise StoreError("At least one field is required")
        with self._session() as session:
            card = self._require_card(session, card_id)
            column = self._require_column(session, card.column_id)
            board = self._require_board(session, column.board_id)
            if data.title is not None:
                card.title = data.title
            if "description" in data.model_fields_set:
                card.description = data.description
            card.updated_at = _now()
            self._touch(board)
            return self._card_out(card)

    def move_card(self, card_id: UUID, data: MoveCardInput) -> Card:
        with self._session() as session:
            card = self._require_card(session, card_id)
            source = self._require_column(session, card.column_id)
            target = self._require_column(session, data.columnId)
            if source.board_id != target.board_id:
                raise StoreError("Cannot move a card to another board")
            source_id = source.id
            card.column_id = target.id
            session.flush()
            self._column_cards(session, source_id)
            targets = [
                item for item in self._column_cards(session, target.id) if item.id != card.id
            ]
            insert_at = min(data.position, len(targets))
            targets.insert(insert_at, card)
            for index, item in enumerate(targets):
                item.position = index
            card.updated_at = _now()
            self._touch(self._require_board(session, target.board_id))
            return self._card_out(card)

    def delete_card(self, card_id: UUID) -> None:
        with self._session() as session:
            card = self._require_card(session, card_id)
            column = self._require_column(session, card.column_id)
            board = self._require_board(session, column.board_id)
            session.delete(card)
            session.flush()
            self._column_cards(session, column.id)
            self._touch(board)
