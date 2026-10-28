import os

# Must be set before importing app modules, so settings point at the test database.
os.environ["ENV"] = "test"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlmodel import Session  # noqa: E402

import app.models  # noqa: E402, F401  (register all models on Base.metadata)
from app.config import get_settings  # noqa: E402
from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

pytest_plugins = [
    "tests.fixtures.todo_fixtures",
]

settings = get_settings()
TEST_DB_URL = make_url(settings.database_url)
# Maintenance database, used to create/drop the test database.
ADMIN_DB_URL = TEST_DB_URL.set(database="postgres")


def ensure_test_database():
    """Create the test database if it does not exist yet."""
    engine = create_engine(ADMIN_DB_URL, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DB_URL.database},
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_URL.database}"'))
    engine.dispose()


def drop_test_database():
    """Drop the test database, closing any connection still attached to it."""
    engine = create_engine(ADMIN_DB_URL, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(
            text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = :name AND pid <> pg_backend_pid()"
            ),
            {"name": TEST_DB_URL.database},
        )
        conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB_URL.database}"'))
    engine.dispose()


@pytest.fixture(scope="session")
def engine():
    ensure_test_database()
    engine = create_engine(TEST_DB_URL)

    # Temporary: replaced by Alembic migrations later (like create_db_and_tables).
    Base.metadata.create_all(engine)

    yield engine

    engine.dispose()
    drop_test_database()


@pytest.fixture(scope="function")
def db(engine):
    """One session per test; everything it does is rolled back afterwards."""
    connection = engine.connect()
    transaction = connection.begin()

    # "create_savepoint" makes commit/rollback inside the code under test act on
    # a savepoint, so the outer transaction can still undo everything.
    TestSession = sessionmaker(
        bind=connection, class_=Session, join_transaction_mode="create_savepoint"
    )
    session = TestSession()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db):
    """FastAPI test client that uses the test session for every request."""

    # Same contract as app.db.get_db: commit on success, rollback on error.
    def override_get_db():
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
