from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CamelModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Error(CamelModel):
    detail: str


class Card(CamelModel):
    id: UUID
    columnId: UUID
    title: str
    description: Optional[str]
    position: int
    createdAt: datetime
    updatedAt: datetime


class Column(CamelModel):
    id: UUID
    boardId: UUID
    title: str
    position: int
    wipLimit: Optional[int]
    cards: list[Card]


class BoardSummary(CamelModel):
    id: UUID
    name: str
    createdAt: datetime
    updatedAt: datetime


class BoardDetail(BoardSummary):
    columns: list[Column]


def _trim(value: str) -> str:
    return value.strip()


class CreateBoardInput(CamelModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        trimmed = _trim(value)
        if not 1 <= len(trimmed) <= 100:
            raise ValueError("Board name must be 1–100 characters")
        return trimmed


class UpdateBoardInput(CreateBoardInput):
    pass


class CreateColumnInput(CamelModel):
    title: str = Field(min_length=1, max_length=60)
    wipLimit: Optional[int] = Field(default=None, ge=1)

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: str) -> str:
        trimmed = _trim(value)
        if not 1 <= len(trimmed) <= 60:
            raise ValueError("Column title must be 1–60 characters")
        return trimmed


class UpdateColumnInput(CamelModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=60)
    wipLimit: Optional[int] = Field(default=None, ge=1)
    position: Optional[int] = Field(default=None, ge=0)

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        trimmed = _trim(value)
        if not 1 <= len(trimmed) <= 60:
            raise ValueError("Column title must be 1–60 characters")
        return trimmed


class CreateCardInput(CamelModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, min_length=1, max_length=2000)

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: str) -> str:
        trimmed = _trim(value)
        if not 1 <= len(trimmed) <= 200:
            raise ValueError("Card title must be 1–200 characters")
        return trimmed

    @field_validator("description")
    @classmethod
    def trim_description(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = _trim(value)
        if trimmed == "":
            return None
        if len(trimmed) > 2000:
            raise ValueError("Description must be 1–2000 characters")
        return trimmed


class UpdateCardInput(CamelModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        trimmed = _trim(value)
        if not 1 <= len(trimmed) <= 200:
            raise ValueError("Card title must be 1–200 characters")
        return trimmed

    @field_validator("description")
    @classmethod
    def trim_description(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = _trim(value)
        return None if trimmed == "" else trimmed


class MoveCardInput(CamelModel):
    columnId: UUID
    position: int = Field(ge=0)
