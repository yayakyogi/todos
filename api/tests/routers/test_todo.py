import uuid

from sqlalchemy import select

from app.models.todo import Todo

# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def test_create_todo(client):
    response = client.post("/todos", json={"title": "Buy milk"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Buy milk"
    assert data["status"] == "open"
    assert data["description"] is None
    assert data["completed_at"] is None
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


def test_create_todo_title_required(client):
    response = client.post("/todos", json={})
    assert response.status_code == 422


def test_create_todo_title_too_long(client):
    response = client.post("/todos", json={"title": "x" * 256})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# List / Get
# ---------------------------------------------------------------------------


def test_list_todos(client, setup_todo, setup_completed_todo):
    response = client.get("/todos")
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert str(setup_todo.id) in ids
    assert str(setup_completed_todo.id) in ids


def test_list_todos_excludes_soft_deleted(client, setup_todo, setup_deleted_todo):
    response = client.get("/todos")
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert str(setup_todo.id) in ids
    assert str(setup_deleted_todo.id) not in ids


def test_get_todo(client, setup_todo):
    response = client.get(f"/todos/{setup_todo.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(setup_todo.id)


def test_get_todo_not_found(client):
    response = client.get(f"/todos/{uuid.uuid4()}")
    assert response.status_code == 404


def test_get_todo_invalid_id(client):
    response = client.get("/todos/not-a-uuid")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def test_update_todo(client, setup_todo):
    response = client.put(
        f"/todos/{setup_todo.id}",
        json={"title": "Renamed", "status": "completed"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Renamed"
    assert data["status"] == "completed"

    # The change must be persisted, not only returned
    response = client.get(f"/todos/{setup_todo.id}")
    assert response.json()["title"] == "Renamed"


def test_update_todo_partial_keeps_other_fields(client, db, setup_todo):
    setup_todo.description = "keep me"
    db.commit()

    response = client.put(f"/todos/{setup_todo.id}", json={"title": "Only title"})
    assert response.status_code == 200
    assert response.json()["description"] == "keep me"


def test_update_todo_invalid_status(client, setup_todo):
    response = client.put(f"/todos/{setup_todo.id}", json={"status": "asdf"})
    assert response.status_code == 422


def test_update_todo_not_found(client):
    response = client.put(f"/todos/{uuid.uuid4()}", json={"title": "Nope"})
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_todo(client, setup_todo):
    response = client.delete(f"/todos/{setup_todo.id}")
    assert response.status_code == 204
    assert response.content == b""

    # Soft-deleted todo should no longer be found
    response = client.get(f"/todos/{setup_todo.id}")
    assert response.status_code == 404


def test_delete_todo_is_soft_delete(client, db, setup_todo):
    """The row stays in the database with deleted_at set."""
    client.delete(f"/todos/{setup_todo.id}")

    db.expire_all()
    todo = db.scalars(
        select(Todo)
        .where(Todo.id == setup_todo.id)
        .execution_options(skip_soft_delete_filter=True)
    ).one()
    assert todo.deleted_at is not None


def test_delete_todo_not_found(client):
    response = client.delete(f"/todos/{uuid.uuid4()}")
    assert response.status_code == 404


def test_delete_todo_twice_returns_404(client, setup_todo):
    assert client.delete(f"/todos/{setup_todo.id}").status_code == 204
    assert client.delete(f"/todos/{setup_todo.id}").status_code == 404
