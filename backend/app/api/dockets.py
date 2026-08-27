"""Saved dockets for the signed-in user. Queries are always scoped by user id."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_docket_store
from app.auth import require_user
from app.schemas.dockets import DocketListResponse, SavedDocket
from app.storage.dockets import DocketStore, SavedDocketRecord

router = APIRouter()


def _to_schema(record: SavedDocketRecord) -> SavedDocket:
    return SavedDocket(id=record.id, saved_at=record.saved_at, result=record.result)


@router.get(
    "/dockets",
    response_model=DocketListResponse,
    summary="List saved dockets for the signed-in user",
)
def list_dockets(
    user_id: str = Depends(require_user),
    store: DocketStore = Depends(get_docket_store),
) -> DocketListResponse:
    records = store.list_for_user(user_id)
    return DocketListResponse(dockets=[_to_schema(item) for item in records])


@router.get(
    "/dockets/{docket_id}",
    response_model=SavedDocket,
    summary="Load one saved docket owned by the signed-in user",
)
def get_docket(
    docket_id: str,
    user_id: str = Depends(require_user),
    store: DocketStore = Depends(get_docket_store),
) -> SavedDocket:
    record = store.get_for_user(user_id, docket_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docket not found.",
        )
    return _to_schema(record)


@router.delete(
    "/dockets/{docket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a saved docket owned by the signed-in user",
)
def delete_docket(
    docket_id: str,
    user_id: str = Depends(require_user),
    store: DocketStore = Depends(get_docket_store),
) -> None:
    deleted = store.delete_for_user(user_id, docket_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Docket not found.",
        )
