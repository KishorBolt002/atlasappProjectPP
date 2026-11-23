from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from src.auth import get_signed_in_email
from src.dependencies import get_db
from src.models import Note
from src.schemas import NoteCreate, NoteResponse, NoteUpdate

router = APIRouter(
    prefix="/api/notes",
    tags=["notes"],
    dependencies=[Depends(get_signed_in_email)],
)

DbSession = Annotated[Session, Depends(get_db)]


def _get_note_or_404(db: Session, note_id: int) -> Note:
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.get("/", response_model=list[NoteResponse])
def list_notes(db: DbSession) -> list[Note]:
    return db.query(Note).order_by(Note.created_at.desc(), Note.id.desc()).all()


@router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(payload: NoteCreate, db: DbSession) -> Note:
    note = Note(title=payload.title, body=payload.body)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(note_id: int, db: DbSession) -> Note:
    return _get_note_or_404(db, note_id)


@router.put("/{note_id}", response_model=NoteResponse)
def update_note(note_id: int, payload: NoteUpdate, db: DbSession) -> Note:
    note = _get_note_or_404(db, note_id)
    note.title = payload.title
    note.body = payload.body
    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: DbSession) -> Response:
    note = _get_note_or_404(db, note_id)
    db.delete(note)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
