from uuid import uuid4

from sqlalchemy import Column, Date, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.constants.todo import TodoStatus
from app.db import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class Todo(Base, TimestampMixin, SoftDeleteMixin):
    """A single actionable task."""

    __tablename__ = "todos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, nullable=False, default=TodoStatus.OPEN)
    due_date = Column(Date, nullable=True)
    completed_at = Column(DateTime, nullable=True)
