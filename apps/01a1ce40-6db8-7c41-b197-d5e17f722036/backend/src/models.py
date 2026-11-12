"""
Database models for the application.

This file contains all SQLAlchemy models. You can freely add, modify, or remove
models in this file. The database connection and configuration is handled in
database.py and should not be modified.

Example model:

    from sqlalchemy import Column, Integer, String, Boolean, DateTime
    from sqlalchemy.sql import func
    from .database import Base

    class Todo(Base):
        __tablename__ = "todos"

        id = Column(Integer, primary_key=True, index=True)
        title = Column(String, index=True)
        description = Column(String, nullable=True)
        completed = Column(Boolean, default=False)
        created_at = Column(DateTime(timezone=True), server_default=func.now())
        updated_at = Column(DateTime(timezone=True), onupdate=func.now())
"""


# Add your models below this line
# All models should inherit from Base imported from database.py

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.database import Base


class Note(Base):
    __tablename__ = "notes"
    __table_args__ = ({"info": {"ontology": "note"}},)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
