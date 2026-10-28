# Todos

[![CI](https://github.com/yayakyogi/todos/actions/workflows/ci.yml/badge.svg)](https://github.com/yayakyogi/todos/actions/workflows/ci.yml)

A small full-stack todo app, organised as a monorepo:

- **`api/`**: a REST API built with FastAPI, SQLAlchemy and PostgreSQL.
- **`web/`**: a single-page app built with SvelteKit that talks to the API.

Docker Compose runs everything (database, API and web app) with one command, in a
**development** mode with hot reload or a **production-like** mode served by nginx.

The API follows the conventions of [linden-api](https://github.com/mylinden-tech/linden-api):
one model per file, separate Pydantic schemas, timestamp and soft-delete mixins, and one
database transaction per request.

## Features

- Create, list, update and delete todos
- Todo status (`open` / `completed`), optional description and due date
- Soft delete: deleted todos are hidden from every query but stay in the database
- `created_at` / `updated_at` timestamps on every row
- Interactive API docs (Swagger UI) at `/docs`

## Tech stack

| Layer | Technology |
|---|---|
| API | Python 3.14, FastAPI 0.141, Uvicorn 0.52 |
| Database access | SQLAlchemy 2.1 (models), SQLModel 0.0.48 (session), psycopg 3 |
| Validation & config | Pydantic 2, pydantic-settings |
| Database | PostgreSQL 18 |
| Web app | SvelteKit 3 (SPA mode), Svelte 5 (runes), TypeScript 6, Vite 8 |
| Package managers | Poetry 2.4 (API), bun 1.4 (web) |
| Production web server | nginx (serves the SPA, proxies `/api`) |
| Tests | pytest 9, FastAPI `TestClient` (httpx2) |
| Runtime | Docker Compose |

## Repository layout

```
todos/
├── api/                    # FastAPI project → see api/README.md
│   ├── app/                # application code (config, db, models, schemas, routers)
│   ├── tests/              # pytest suite
│   └── Dockerfile          # targets: dev, prod
├── web/                    # SvelteKit SPA → see web/README.md
│   ├── src/                # routes and the API client
│   ├── nginx.conf          # production server config
│   └── Dockerfile          # targets: dev, build, prod
├── docs/                   # architecture, Docker and testing guides
├── compose.yaml            # base services: db, api, web
├── compose.override.yaml   # development settings (loaded automatically)
├── compose.prod.yaml       # production-like settings
└── .env.example            # variables for Docker Compose
```

## Quick start

Requirements: [Docker](https://docs.docker.com/get-docker/) with Compose v2.

```bash
cp .env.example .env
docker compose up --build
```

Then open:

| URL | What |
|---|---|
| http://localhost:5173 | Web app |
| http://localhost:8000/docs | API docs (Swagger UI) |
| `localhost:5433` | PostgreSQL (user `postgres`, password `postgres`, database `todo`) |

Code in `api/` and `web/` is mounted into the containers, so changes reload automatically.
Stop with `Ctrl+C`, or with `docker compose down` if you ran it with `-d`.

## Common commands

| Task | Command |
|---|---|
| Start in development mode | `docker compose up --build` |
| Start production-like (http://localhost:8080) | `docker compose -f compose.yaml -f compose.prod.yaml up --build` |
| Run the API tests | `docker compose exec api pytest` |
| Show logs | `docker compose logs -f api web` |
| Stop | `docker compose down` |
| Stop and delete the database | `docker compose down -v` |

To use an **external database** instead of the bundled Postgres, set `COMPOSE_PROFILES=` (empty)
and point `DATABASE_URL` at your database in `.env`. See [docs/docker.md](docs/docker.md#using-an-external-database).

You can also run each project without Docker; see [api/README.md](api/README.md) and
[web/README.md](web/README.md).

## Dependency updates

[Renovate](https://docs.renovatebot.com/) (Mend Renovate GitHub App) opens a pull request for
every outdated dependency: Python packages (`api/pyproject.toml`), web packages
(`web/package.json`), Docker images (Dockerfiles and `compose.yaml`) and GitHub Actions.
CI runs on each of these PRs; merge them once the checks are green. The **Dependency Dashboard**
issue lists all pending updates. Configuration: [`renovate.json`](renovate.json).

To track a version that Renovate does not detect on its own, put a comment above it, as done
for Poetry in `api/Dockerfile` and `.github/workflows/ci.yml`:

```dockerfile
# renovate: datasource=pypi depName=poetry
ARG POETRY_VERSION=2.4.1
```

## Documentation

| Document | Contents |
|---|---|
| [docs/architecture.md](docs/architecture.md) | How a request flows through the system and why it is built this way |
| [docs/docker.md](docs/docker.md) | Compose files, dev vs prod, environment variables, troubleshooting |
| [docs/testing.md](docs/testing.md) | How the API test suite works and how to add tests |
| [api/README.md](api/README.md) | API layout, endpoints, configuration, adding a new model |
| [web/README.md](web/README.md) | Web app layout, scripts, API client, SvelteKit 3 notes |
# todos
