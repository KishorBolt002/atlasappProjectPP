from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.auth import CurrentUser, get_current_user, require_role
from src.dependencies import get_db
from src.models import AppUser
from src.schemas import MeResponse, UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])

DbSession = Annotated[Session, Depends(get_db)]
Admin = Annotated[CurrentUser, Depends(require_role("admin"))]


@router.get("/me", response_model=MeResponse)
def get_me(user: Annotated[CurrentUser, Depends(get_current_user)]) -> MeResponse:
    return MeResponse(
        email=user.email, name=user.name, role=user.role, is_admin=user.role == "admin"
    )


@router.get("/", response_model=list[UserResponse])
def list_users(db: DbSession, _: Admin) -> list[AppUser]:
    return db.query(AppUser).order_by(AppUser.email).all()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: DbSession, _: Admin) -> AppUser:
    exists = (
        db.query(AppUser).filter(func.lower(AppUser.email) == payload.email).first()
    )
    if exists:
        raise HTTPException(
            status_code=409, detail="A user with this email already exists"
        )
    user = AppUser(email=payload.email, name=payload.name, role=payload.role)
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="A user with this email already exists"
        ) from exc
    db.refresh(user)
    return user


def _get_user(db: Session, user_id: int) -> AppUser:
    user = db.get(AppUser, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _admin_count(db: Session) -> int:
    # Lock admin rows so concurrent demotions/removals can't both pass the check.
    return len(
        db.query(AppUser.id).filter(AppUser.role == "admin").with_for_update().all()
    )


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int, payload: UserUpdate, db: DbSession, admin: Admin
) -> AppUser:
    user = _get_user(db, user_id)
    if user.role == "admin" and payload.role != "admin" and _admin_count(db) <= 1:
        raise HTTPException(status_code=409, detail="The app needs at least one admin")
    user.role = payload.role
    if payload.name is not None:
        user.name = payload.name
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: DbSession, _: Admin) -> Response:
    user = _get_user(db, user_id)
    if user.role == "admin" and _admin_count(db) <= 1:
        raise HTTPException(status_code=409, detail="The app needs at least one admin")
    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
