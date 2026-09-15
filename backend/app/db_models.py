from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BoardRow(Base):
    __tablename__ = "boards"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    columns: Mapped[list[ColumnRow]] = relationship(
        back_populates="board",
        cascade="all, delete-orphan",
        order_by="ColumnRow.position",
    )


class ColumnRow(Base):
    __tablename__ = "columns"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    board_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("boards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(60), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    wip_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    board: Mapped[BoardRow] = relationship(back_populates="columns")
    cards: Mapped[list[CardRow]] = relationship(
        back_populates="column",
        cascade="all, delete-orphan",
        order_by="CardRow.position",
    )


class CardRow(Base):
    __tablename__ = "cards"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    column_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("columns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    column: Mapped[ColumnRow] = relationship(back_populates="cards")
