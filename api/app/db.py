from collections.abc import Generator, Iterator
from contextlib import contextmanager
from typing import Annotated

from fastapi import Depends
from sqlalchemy import event
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import declarative_base, sessionmaker, with_loader_criteria
from sqlmodel import Session, create_engine

from app.config import get_settings

# Parent class for every table model.
Base = declarative_base()


@event.listens_for(OrmSession, "do_orm_execute")
def _add_soft_delete_criteria(execute_state):
    """Automatically filter out soft-deleted records from all queries."""
    from app.models.mixins import SoftDeleteMixin

    skip_filter = execute_state.execution_options.get("skip_soft_delete_filter", False)

    if execute_state.is_select and not skip_filter:
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                SoftDeleteMixin,
                lambda cls: cls.deleted_at.is_(None),
                include_aliases=True,
            )
        )


# Read once at import time, so ENV=test must be set before importing this module.
settings = get_settings()

# One engine per app; it owns the connection pool (no connection is opened yet).
engine = create_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,  # connections kept open
    max_overflow=settings.database_max_overflow,  # extra connections under load
    pool_pre_ping=True,  # replace dead connections before use
    pool_recycle=300,  # renew connections older than 5 minutes
    pool_use_lifo=True,  # reuse the newest connection so idle ones can close
    connect_args={"application_name": settings.app_name},  # label in pg_stat_activity
)

# Session factory; autoflush sends pending changes before each query.
SessionLocal = sessionmaker(bind=engine, class_=Session, autoflush=True)


def create_db_and_tables() -> None:
    import app.models  # noqa: F401 (register all models on Base.metadata)

    # Temporary: replaced by Alembic migrations later.
    Base.metadata.create_all(engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    """One unit of work: commit on success, rollback on error, always close."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise  # never swallow the error
    finally:
        session.close()  # return the connection to the pool


# FastAPI dependency: one session (one transaction) per request.
def get_db() -> Generator[Session, None, None]:
    with session_scope() as session:
        yield session


# scope="function": commit runs before the response is sent, not after.
DbSession = Annotated[Session, Depends(get_db, scope="function")]
