# Testing

## Running the tests

The API tests run against a **real PostgreSQL database**, never against your development data.

```bash
# Inside Docker (uses the bundled Postgres)
docker compose exec api pytest

# Locally (needs Postgres on localhost:5432, see api/.env)
cd api
poetry run pytest
```

Useful pytest options: `-q` for short output, `-k delete` to run tests whose name contains
"delete", `-x` to stop at the first failure.

## How the test setup works

Everything lives in `api/tests/conftest.py`.

### 1. The test database

`conftest.py` sets `ENV=test` **before** importing the app. `app/config.py` then replaces
`DATABASE_URL` with `TEST_DATABASE_URL` (`todo_test`), so nothing in the tests can touch the
development database.

The session-scoped `engine` fixture runs once per test run:

1. Connects to the `postgres` maintenance database and creates `todo_test` if it does not exist.
2. Creates all tables with `Base.metadata.create_all()`.
3. After the last test, drops `todo_test` again.

### 2. A clean database for every test

The `db` fixture gives each test its own session inside a transaction that is **rolled back**
when the test ends, so tests never see each other's data and need no cleanup code.

```python
connection = engine.connect()
transaction = connection.begin()
session = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")()
```

`join_transaction_mode="create_savepoint"` is the key: when the code under test (or a fixture)
calls `commit()`, it only releases a **savepoint**, and the outer transaction can still undo
everything. linden-api uses the same pattern.

### 3. The HTTP client

The `client` fixture returns a FastAPI `TestClient` and overrides the `get_db` dependency so
that every request uses the test session. The override keeps the same contract as the real
`get_db` in `app/db.py`: commit on success, roll back on error.

Note that the client and the test share **one session**. That makes the identity-map pitfall
described in [architecture.md](architecture.md#soft-delete) visible in tests, which is how the
`session.get()` soft-delete bug was found.

### 4. Fixtures

Data fixtures live in `api/tests/fixtures/<name>_fixtures.py` and are registered in
`conftest.py` through `pytest_plugins`. `todo_fixtures.py` provides:

| Fixture | Creates |
|---|---|
| `setup_todo` | an open todo |
| `setup_completed_todo` | a completed todo with `completed_at` set |
| `setup_deleted_todo` | a soft-deleted todo |

## What is covered

`api/tests/routers/test_todo.py` covers every endpoint:

- **Create:** success, missing title, title longer than 255 characters
- **List / get:** list contents, soft-deleted todos excluded, not found, invalid UUID
- **Update:** changes are persisted, partial updates keep other fields, invalid status, not found
- **Delete:** returns 204 with no body, the row stays with `deleted_at` set, not found, deleting twice

## Adding tests

1. If you need new data, add a fixture to `api/tests/fixtures/<name>_fixtures.py`. For a new
   file, add it to `pytest_plugins` in `conftest.py`.
2. Add a test function to `api/tests/routers/test_<name>.py` that takes the fixtures it needs:

   ```python
   def test_update_todo_description(client, setup_todo):
       response = client.put(
           f"/todos/{setup_todo.id}", json={"description": "Two litres"}
       )
       assert response.status_code == 200
       assert response.json()["description"] == "Two litres"
   ```

3. Assert on what the user observes (status code, response body), and when it matters, also
   check that the change was persisted, for example with a follow-up `GET` or a query on `db`.

To look at rows the soft-delete filter hides, query with
`.execution_options(skip_soft_delete_filter=True)`; see `test_delete_todo_is_soft_delete`.

## Web app

The web app has no automated tests yet. Type-check it with:

```bash
cd web
bun run check
```
