from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.db import DbSession
from app.models import Todo
from app.schemas.todo import TodoCreate, TodoResponse, TodoUpdate

router = APIRouter(prefix="/todos", tags=["todos"])


def get_todo_or_404(todo_id: UUID, session: DbSession) -> Todo:
    # Use a SELECT instead of session.get(): session.get() returns objects from the
    # identity map without querying, which skips the soft-delete filter.
    todo = session.scalars(select(Todo).where(Todo.id == todo_id)).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.get("", response_model=list[TodoResponse])
def list_todos(session: DbSession):
    return session.scalars(select(Todo)).all()


@router.post("", response_model=TodoResponse, status_code=201)
def create_todo(todo: TodoCreate, session: DbSession):
    new_todo = Todo(**todo.model_dump())
    session.add(new_todo)
    session.flush()
    session.refresh(new_todo)
    return new_todo


@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: UUID, session: DbSession):
    return get_todo_or_404(todo_id, session)


@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: UUID, update: TodoUpdate, session: DbSession):
    todo = get_todo_or_404(todo_id, session)
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(todo, key, value)
    session.add(todo)
    session.flush()
    session.refresh(todo)
    return todo


@router.delete("/{todo_id}", status_code=204)
def delete_todo(todo_id: UUID, session: DbSession):
    todo = get_todo_or_404(todo_id, session)
    todo.deleted_at = datetime.now(UTC)
    session.flush()
