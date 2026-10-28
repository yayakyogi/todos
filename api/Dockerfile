FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Install dependencies into the system Python; the container is the isolation.
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

RUN pip install --no-cache-dir poetry==2.4.1

WORKDIR /app

# Copy only dependency files first, so this layer is cached until they change.
COPY pyproject.toml poetry.lock ./


# Development: all dependencies (incl. pytest), source is mounted by compose.
FROM base AS dev

RUN poetry install --no-cache

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# Production: runtime dependencies only, source baked into the image.
FROM base AS prod

RUN poetry install --only main --no-cache

COPY app ./app

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
