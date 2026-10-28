# Todos API

REST API for the todo app, built with FastAPI, SQLAlchemy and PostgreSQL.
For the whole project, see the [root README](../README.md).

## Layout

```
api/
├── app/
│   ├── main.py            # FastAPI app, lifespan, router registration
│   ├── config.py          # Settings from env vars / .env
│   ├── db.py              # Engine, sessions, transaction boundary, soft-delete filter, Base
│   ├── constants/         # Fixed values (e.g. TodoStatus)
│   ├── models/            # SQLAlchemy table models, one per file
│   │   └── mixins.py      # TimestampMixin, SoftDeleteMixin
│   ├── schemas/           # Pydantic request/response models
│   └── routers/           # HTTP endpoints
├── tests/                 # pytest suite, see ../docs/testing.md
├── Dockerfile             # targets: dev, prod
└── pyproject.toml         # dependencies (Poetry)
```

How these layers work together is explained in [docs/architecture.md](../docs/architecture.md#api).

## Running without Docker

Requirements: Python 3.14, [Poetry](https://python-poetry.org/) 2, and a PostgreSQL server.

```bash
cd api
cp .env.example .env        # adjust DATABASE_URL if needed
poetry install
poetry run uvicorn app.main:app --reload
```

The API runs on http://localhost:8000, with interactive docs at http://localhost:8000/docs.
The database in `DATABASE_URL` must exist; tables are created on startup.

To use the Postgres from Docker Compose instead of a local one, run `docker compose up db`
from the repository root and set the host and port in `api/.env` to `localhost:5433`.

## Endpoints

| Method | Path | Body | Success | Errors |
|---|---|---|---|---|
| `GET` | `/todos` | — | `200` list of todos | — |
| `POST` | `/todos` | `TodoCreate` | `201` created todo | `422` invalid body |
| `GET` | `/todos/{id}` | — | `200` todo | `404` not found or deleted, `422` invalid UUID |
| `PUT` | `/todos/{id}` | `TodoUpdate` (partial) | `200` updated todo | `404`, `422` |
| `DELETE` | `/todos/{id}` | — | `204` no content (soft delete) | `404` |

Request and response shapes are defined in `app/schemas/todo.py`:

- **`TodoCreate`**: `title` (required, max 255), `description`, `due_date`
- **`TodoUpdate`**: any of `title`, `description`, `status` (`"open"` or `"completed"`), `due_date`.
  Only the fields you send are changed.
- **`TodoResponse`**: `id`, `title`, `description`, `status`, `due_date`, `completed_at`,
  `created_at`, `updated_at`

## Configuration

Settings are defined in `app/config.py` and read from environment variables or `api/.env`.
Environment variables win over the file.

| Variable | Default | Description |
|---|---|---|
| `ENV` (or `ENVIRONMENT`) | `development` | `test` switches `DATABASE_URL` to `TEST_DATABASE_URL` |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/todo` | Main database |
| `TEST_DATABASE_URL` | `...@localhost:5432/todo_test` | Database used by the tests |
| `DATABASE_POOL_SIZE` | `10` | Connections kept open in the pool |
| `DATABASE_MAX_OVERFLOW` | `20` | Extra connections allowed under load |
| `LOG_LEVEL` | `INFO` | Log level setting |
| `PORT` | `8000` | Setting only; the port Uvicorn listens on comes from its `--port` option |

## Adding a new model

Follow the same steps as `Todo`. Using a `Tag` model as an example:

1. **Constants** (if needed): `app/constants/tag.py`.
2. **Model**: `app/models/tag.py`, a class inheriting from `Base` (from `app.db`) plus
   `TimestampMixin` / `SoftDeleteMixin`, with `__tablename__ = "tags"` and a UUID `id`.
3. **Register** it in `app/models/__init__.py` (import and `__all__`), so
   `create_all()` knows about the table.
4. **Schemas**: `app/schemas/tag.py` with `TagCreate`, `TagUpdate` and `TagResponse`
   (`model_config = ConfigDict(from_attributes=True)`).
5. **Router**: `app/routers/tags.py`. Load single rows with `select()` (not `session.get()`),
   use `session.flush()` instead of `commit()`, and include it in `app/main.py` with
   `app.include_router(tags.router)`.
6. **Tests**: fixtures in `tests/fixtures/tag_fixtures.py` (added to `pytest_plugins`) and
   tests in `tests/routers/test_tag.py`. See [docs/testing.md](../docs/testing.md).

`create_all()` only creates missing tables. After changing an existing model, drop its table
(or reset the Docker database with `docker compose down -v`) until Alembic migrations are added.

## Tests

```bash
poetry run pytest
```

See [docs/testing.md](../docs/testing.md) for how the test database and fixtures work.
