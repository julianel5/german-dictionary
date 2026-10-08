"""GET /api/entries/{id} and its sub-resources."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.deps import SessionDep
from app.schemas.entries import EntryDetailResponse, ExamplesResponse, FormsResponse
from app.services.entry_service import EntryNotFoundError, EntryService

router = APIRouter(tags=["entries"])


@router.get("/entries/{lexeme_id}", response_model=EntryDetailResponse)
def get_entry(lexeme_id: str, session: SessionDep) -> EntryDetailResponse:
    try:
        return EntryService(session).entry(lexeme_id)
    except EntryNotFoundError:
        raise HTTPException(status_code=404, detail="Entry not found") from None


@router.get("/entries/{lexeme_id}/forms", response_model=FormsResponse)
def get_entry_forms(lexeme_id: str, session: SessionDep) -> FormsResponse:
    try:
        return EntryService(session).forms(lexeme_id)
    except EntryNotFoundError:
        raise HTTPException(status_code=404, detail="Entry not found") from None


@router.get("/entries/{lexeme_id}/examples", response_model=ExamplesResponse)
def get_entry_examples(lexeme_id: str, session: SessionDep) -> ExamplesResponse:
    try:
        return EntryService(session).examples(lexeme_id)
    except EntryNotFoundError:
        raise HTTPException(status_code=404, detail="Entry not found") from None
