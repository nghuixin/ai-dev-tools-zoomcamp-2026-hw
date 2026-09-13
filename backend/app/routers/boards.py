from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.deps import get_store
from app.errors import StoreError
from app.models import BoardDetail, BoardSummary, Column, CreateBoardInput, CreateColumnInput, UpdateBoardInput
from app.store import Store

router = APIRouter(tags=["boards"])


def _run(store_call):
    try:
        return store_call()
    except StoreError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.detail) from exc


@router.get("/boards", operation_id="listBoards")
def list_boards(store: Annotated[Store, Depends(get_store)]) -> list[BoardSummary]:
    return store.list_boards()


@router.post("/boards", status_code=status.HTTP_201_CREATED, operation_id="createBoard")
def create_board(
    data: CreateBoardInput,
    store: Annotated[Store, Depends(get_store)],
) -> BoardDetail:
    return _run(lambda: store.create_board(data))


@router.get("/boards/{id}", operation_id="getBoard")
def get_board(id: UUID, store: Annotated[Store, Depends(get_store)]) -> BoardDetail:
    return _run(lambda: store.get_board(id))


@router.patch("/boards/{id}", operation_id="updateBoard")
def update_board(
    id: UUID,
    data: UpdateBoardInput,
    store: Annotated[Store, Depends(get_store)],
) -> BoardDetail:
    return _run(lambda: store.update_board(id, data))


@router.delete("/boards/{id}", status_code=status.HTTP_204_NO_CONTENT, operation_id="deleteBoard")
def delete_board(id: UUID, store: Annotated[Store, Depends(get_store)]) -> Response:
    _run(lambda: store.delete_board(id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/boards/{id}/columns",
    status_code=status.HTTP_201_CREATED,
    operation_id="createColumn",
    tags=["columns"],
)
def create_column(
    id: UUID,
    data: CreateColumnInput,
    store: Annotated[Store, Depends(get_store)],
) -> Column:
    return _run(lambda: store.create_column(id, data))
