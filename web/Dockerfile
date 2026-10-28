FROM oven/bun:1.4 AS base

WORKDIR /app

# Copy only dependency files first, so this layer is cached until they change.
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

COPY . .


# Development: Vite dev server with hot reload, source is mounted by compose.
FROM base AS dev

EXPOSE 5173
CMD ["bun", "run", "dev"]


# Build the static SPA into /app/build.
FROM base AS build

RUN bun run build


# Production: nginx serves the static files and proxies /api to the API.
FROM nginx:stable-alpine AS prod

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80
