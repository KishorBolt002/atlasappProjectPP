"""Test notes stored in the app database, independent of Salesforce."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.dependencies import get_db
from src.models import TestNote
from src.schemas import NoteIn, NoteOut

router = APIRouter(prefix="/api/notes", tags=["notes"])


@router.get("/", response_model=list[NoteOut])
def list_notes(db: Annotated[Session, Depends(get_db)]) -> list[TestNote]:
    return (
        db.query(TestNote)
        .order_by(TestNote.created_at.desc(), TestNote.id.desc())
        .all()
    )


@router.post("/", response_model=NoteOut, status_code=201)
def create_note(payload: NoteIn, db: Annotated[Session, Depends(get_db)]) -> TestNote:
    note = TestNote(text=payload.text)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note
