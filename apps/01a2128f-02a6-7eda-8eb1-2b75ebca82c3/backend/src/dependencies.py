"""
Database dependency for FastAPI routes.

This module provides the get_db dependency that should be used in all routes
that need database access. It properly manages database sessions.
"""

from src.database import SessionLocal


def get_db():
    """
    Database dependency for FastAPI routes.

    Yields a database session and ensures it's properly closed after use.

    Usage:
        from typing import Annotated

        from ..dependencies import get_db
        from fastapi import Depends
        from sqlalchemy.orm import Session

        @router.get("/items")
        def get_items(db: Annotated[Session, Depends(get_db)]):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
