from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.deps import get_store
from app.errors import StoreError
from app.models import Card, Column, CreateCardInput, UpdateColumnInput
from app.store import Store

router = APIRouter(tags=["columns"])


def _run(store_call):
    try:
        return store_call()
    except StoreError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.detail) from exc


@router.patch("/columns/{id}", operation_id="updateColumn")
def update_column(
    id: UUID,
    data: UpdateColumnInput,
    store: Annotated[Store, Depends(get_store)],
) -> Column:
    return _run(lambda: store.update_column(id, data))


@router.delete(
    "/columns/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteColumn",
)
def delete_column(id: UUID, store: Annotated[Store, Depends(get_store)]) -> Response:
    _run(lambda: store.delete_column(id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/columns/{id}/cards",
    status_code=status.HTTP_201_CREATED,
    operation_id="createCard",
    tags=["cards"],
)
def create_card(
    id: UUID,
    data: CreateCardInput,
    store: Annotated[Store, Depends(get_store)],
) -> Card:
    return _run(lambda: store.create_card(id, data))
