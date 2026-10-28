# Todos Web

Single-page app for the todo API, built with SvelteKit 3 and Svelte 5.
For the whole project, see the [root README](../README.md).

## Layout

```
web/
├── src/
│   ├── lib/
│   │   └── api.ts            # API client: types + one function per endpoint
│   ├── routes/
│   │   ├── +layout.ts        # ssr = false (SPA mode)
│   │   ├── +layout.svelte    # shared layout (favicon)
│   │   └── +page.svelte      # the todo list page
│   └── app.html              # HTML shell
├── static/                   # files copied as-is (robots.txt)
├── vite.config.ts            # SvelteKit + adapter config, dev server and /api proxy
├── nginx.conf                # production server config
└── Dockerfile                # targets: dev, build, prod
```

## Running without Docker

Requirements: [bun](https://bun.sh/) 1.4, and the API running (see [api/README.md](../api/README.md)).

```bash
cd web
bun install
bun run dev
```

Open http://localhost:5173. Requests to `/api/*` are forwarded to the API at
`http://localhost:8000` by default. To use another address, set `API_URL`:

```bash
API_URL=http://localhost:9000 bun run dev
```

## Scripts

| Script | What it does |
|---|---|
| `bun run dev` | Dev server with hot reload on port 5173 |
| `bun run build` | Builds the static SPA into `build/` |
| `bun run preview` | Serves `build/` locally to check the production build |
| `bun run check` | Type-checks Svelte and TypeScript files |

## Talking to the API

All API calls go through `src/lib/api.ts`:

```ts
import { createTodo, listTodos } from '#lib/api.ts';

const todos = await listTodos();
const todo = await createTodo({ title: 'Buy milk' });
```

- The types (`Todo`, `TodoCreate`, `TodoUpdate`) mirror the schemas in
  `api/app/schemas/todo.py`. **Update both together** when the API changes.
- Every call uses the relative path `/api/...`, never a full URL. The dev server (Vite proxy)
  or nginx (production) forwards it to the API, so no CORS setup is needed.
  See [docs/architecture.md](../docs/architecture.md#why-a-proxy-instead-of-cors).
- Failed requests throw an `Error` with the status code and the API's `detail` message.

## SvelteKit 3 notes

This project was created with `sv` and uses SvelteKit 3, which differs from older
tutorials in a few places:

- **No `svelte.config.js`.** SvelteKit options (including the adapter) are passed to the
  `sveltekit()` plugin in `vite.config.ts`.
- **`#lib` instead of `$lib`.** The alias is defined in `package.json` `imports` as a Node
  subpath import, so imports need the file extension: `'#lib/api.ts'`, not `'#lib/api'`.
- **Runes mode is forced** for project files (`$state`, `$derived`, `$props`).

## SPA mode

`src/routes/+layout.ts` disables server-side rendering, and `@sveltejs/adapter-static`
builds plain files with `200.html` as the fallback page. Any static file server works, as long
as it serves `200.html` for unknown paths; `nginx.conf` does exactly that. Because there is no
server, `load` functions run in the browser and cannot use secrets.

## Adding a page

Create `src/routes/<name>/+page.svelte`; it is served at `/<name>`. Put shared data access in
`src/lib/` and import it with `#lib/...`. Run `bun run check` before committing.
