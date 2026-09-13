from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.deps import get_store
from app.errors import StoreError
from app.models import Card, MoveCardInput, UpdateCardInput
from app.store import Store

router = APIRouter(tags=["cards"])


def _run(store_call):
    try:
        return store_call()
    except StoreError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.detail) from exc


@router.patch("/cards/{id}", operation_id="updateCard")
def update_card(
    id: UUID,
    data: UpdateCardInput,
    store: Annotated[Store, Depends(get_store)],
) -> Card:
    return _run(lambda: store.update_card(id, data))


@router.post("/cards/{id}/move", operation_id="moveCard")
def move_card(
    id: UUID,
    data: MoveCardInput,
    store: Annotated[Store, Depends(get_store)],
) -> Card:
    return _run(lambda: store.move_card(id, data))


@router.delete("/cards/{id}", status_code=status.HTTP_204_NO_CONTENT, operation_id="deleteCard")
def delete_card(id: UUID, store: Annotated[Store, Depends(get_store)]) -> Response:
    _run(lambda: store.delete_card(id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
