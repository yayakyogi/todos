from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TodoCreate(BaseModel):
    """Request body for POST /todos"""

    title: str = Field(..., max_length=255)
    description: str | None = None
    due_date: date | None = None


class TodoUpdate(BaseModel):
    """Request body for PUT /todos/{id}"""

    title: str | None = Field(None, max_length=255)
    description: str | None = None
    status: Literal["open", "completed"] | None = None
    due_date: date | None = None


class TodoResponse(BaseModel):
    """Response schema for a Todo"""

    id: UUID
    title: str
    description: str | None
    status: str
    due_date: date | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    # Allows building the response directly from an ORM object
    model_config = ConfigDict(from_attributes=True)

