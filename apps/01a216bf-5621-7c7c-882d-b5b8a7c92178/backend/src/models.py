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
