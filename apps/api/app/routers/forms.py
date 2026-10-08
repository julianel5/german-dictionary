"""GET /api/forms/{id}"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.deps import SessionDep
from app.schemas.entries import WordFormDTO
from app.services.entry_service import EntryNotFoundError, EntryService

router = APIRouter(tags=["forms"])


@router.get("/forms/{word_form_id}", response_model=WordFormDTO)
def get_form(word_form_id: str, session: SessionDep) -> WordFormDTO:
    try:
        return EntryService(session).form(word_form_id)
    except EntryNotFoundError:
        raise HTTPException(status_code=404, detail="Form not found") from None
