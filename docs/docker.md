# Docker

Everything runs with Docker Compose. This document explains the Compose files, the two
modes, the environment variables and common problems.

## Compose files

| File | Purpose | Loaded |
|---|---|---|
| `compose.yaml` | Base services shared by every mode: `db`, `api`, `web` | always |
| `compose.override.yaml` | Development: source mounts, hot reload, published ports | automatically by `docker compose ...` |
| `compose.prod.yaml` | Production-like: code baked into images, nginx, only one port | only with `-f compose.yaml -f compose.prod.yaml` |

Compose merges the files from left to right. When you pass `-f` explicitly, the override
file is **not** loaded, which is how the production command skips the development settings.

```bash
# Development
docker compose up --build

# Production-like
docker compose -f compose.yaml -f compose.prod.yaml up --build
```

Both modes read `.env` in the repository root. Create it first:

```bash
cp .env.example .env
```

## Services

| Service | Image | Port (dev) | Port (prod) | Healthcheck | Starts after |
|---|---|---|---|---|---|
| `db` | `postgres:18-alpine` | `5433` → 5432 | not published | `pg_isready` | — |
| `api` | `todos-api:dev` / `todos-api:prod` (built from `api/Dockerfile`) | `8000` | not published | `GET /` | `db` is healthy (if enabled) |
| `web` | `todos-web:dev` / `todos-web:prod` (built from `web/Dockerfile`) | `5173` | `8080` → 80 | — | `api` is healthy |

- `db` belongs to the `db` **profile**, so it only starts when `COMPOSE_PROFILES` contains `db`
  (the default in `.env.example`).
- `api` depends on `db` with `required: false`, so the API can also start when the `db`
  service is disabled (external database).
- `web` waits until `api` is healthy, so the first requests through the proxy do not fail.

## Development vs production

| | Development | Production-like |
|---|---|---|
| API image target | `dev`: all dependencies, including pytest | `prod`: runtime dependencies only, runs as non-root `appuser` |
| API process | `uvicorn --reload` | `uvicorn --proxy-headers` |
| API source | `./api` mounted at `/app` | copied into the image |
| Web image target | `dev`: Vite dev server | `prod`: nginx with the built SPA |
| Web source | `./web` mounted at `/app` | built during `docker build` |
| Published ports | web 5173, API 8000, db 5433 | web 8080 only |
| `ENV` | `development` (from `.env`) | `production` |

In development, `node_modules` and `.svelte-kit` inside the web container are **anonymous
volumes**. This keeps the container's Linux dependencies separate from anything on your Mac.

### Dockerfile targets

- **`api/Dockerfile`**: `base` (Python 3.14 + Poetry, dependency files copied first for layer
  caching) → `dev` or `prod`.
- **`web/Dockerfile`**: `base` (bun, `bun install --frozen-lockfile`) → `dev`, or `build`
  (`bun run build`) → `prod` (`nginx:stable-alpine` + `web/nginx.conf` + `build/`).

## Environment variables

All variables live in the root `.env` (copied from `.env.example`).

| Variable | Default | Used for |
|---|---|---|
| `COMPOSE_PROFILES` | `db` | Starts the bundled Postgres. Empty = no `db` container |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `postgres` / `postgres` / `todo` | Bundled Postgres credentials |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@db:5432/todo` | Database the API uses |
| `TEST_DATABASE_URL` | `...@db:5432/todo_test` | Database the tests create and drop |
| `ENV` | `development` | API environment (`development`, `test`, `production`) |
| `LOG_LEVEL` | `INFO` | API log level setting |
| `API_PORT` | `8000` | Host port for the API (dev) |
| `WEB_DEV_PORT` | `5173` | Host port for the Vite dev server (dev) |
| `WEB_PORT` | `8080` | Host port for nginx (prod) |
| `DB_HOST_PORT` | `5433` | Host port for the bundled Postgres (dev) |

Inside the Compose network, containers reach each other by **service name**: the API connects
to `db:5432`, and the web container forwards to `api:8000`. The host ports above are only for
you (browser, database client).

If you change `POSTGRES_*`, update `DATABASE_URL` and `TEST_DATABASE_URL` to match.

Environment variables set by Compose take precedence over `api/.env`, which is only meant
for running the API without Docker.

## Using an external database

1. In `.env`, disable the bundled database and point `DATABASE_URL` at your server:

   ```dotenv
   COMPOSE_PROFILES=
   DATABASE_URL=postgresql+psycopg://user:password@your-host:5432/todo
   ```

   For a Postgres running on your own machine, use `host.docker.internal` as the host.
   `localhost` would point at the API container itself.

2. Start as usual: `docker compose up --build`. `docker compose ps` should list only `api`
   and `web`.

The API creates its tables on startup, so the database must exist and the user must be
allowed to create tables.

## Data

The bundled Postgres stores its data in the named volume `todos_pgdata`, so todos survive
`docker compose down` and restarts. To start from an empty database:

```bash
docker compose down -v
```

## Troubleshooting

**`Bind for 0.0.0.0:5433 failed: port is already allocated`** (or 8000, 5173, 8080)
Another process uses that port. Change `DB_HOST_PORT`, `API_PORT`, `WEB_DEV_PORT` or `WEB_PORT`
in `.env`. The database is published on 5433 by default because a local Postgres usually
already uses 5432.

**I switched between dev and prod and the wrong thing is running**
Dev and prod use different image tags (`:dev` / `:prod`), so this should not happen. If you
ever see nginx in development, rebuild: `docker compose up --build`.

**I added a package to `web/` and the dev server cannot find it**
`node_modules` is an anonymous volume created from the image. Rebuild the image and recreate
the volume:

```bash
docker compose up --build --renew-anon-volumes web
```

**I added a dependency to `api/`**
Run `poetry add <package>` in `api/`, then `docker compose up --build` to install it in the image.

**`502 Bad Gateway` from nginx**
The API is not reachable. Check `docker compose ps` (is `api` healthy?) and
`docker compose logs api`; a wrong `DATABASE_URL` is the usual cause.

**A new model column does not appear**
`create_all()` does not alter existing tables. Drop the table, or reset the database with
`docker compose down -v`. See [architecture.md](architecture.md#database-schema-management).
