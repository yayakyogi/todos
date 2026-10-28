from datetime import UTC, datetime

import pytest

from app.constants.todo import TodoStatus
from app.models.todo import Todo


@pytest.fixture
def setup_todo(db):
    """Create a test Todo in the database."""
    todo = Todo(title="Test Todo", status=TodoStatus.OPEN)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@pytest.fixture
def setup_completed_todo(db):
    """Create a completed Todo in the database."""
    todo = Todo(
        title="Completed Todo",
        status=TodoStatus.COMPLETED,
        completed_at=datetime.now(UTC),
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@pytest.fixture
def setup_deleted_todo(db):
    """Create a soft-deleted Todo in the database."""
    todo = Todo(title="Deleted Todo", deleted_at=datetime.now(UTC))
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo
