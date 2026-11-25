"""
Pydantic schemas for API request/response validation.

IMPORTANT: Never import from models, crud, services, or routers in this file.
Only import from pydantic, typing, datetime, enum, and standard library.

Example schemas:

    from pydantic import BaseModel, Field, ConfigDict
    from typing import Optional
    from datetime import datetime

    class TodoBase(BaseModel):
        title: str = Field(..., min_length=1, max_length=200)
        description: Optional[str] = None
        completed: bool = False

    class TodoCreate(TodoBase):
        pass

    class TodoUpdate(BaseModel):
        title: Optional[str] = Field(None, min_length=1, max_length=200)
        description: Optional[str] = None
        completed: Optional[bool] = None

    class TodoResponse(TodoBase):
        id: int
        created_at: datetime
        updated_at: Optional[datetime] = None

        model_config = ConfigDict(from_attributes=True)
"""


# Add your schemas below this line
# Follow the pattern: Base, Create, Update, Response for each model
