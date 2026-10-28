from datetime import UTC, datetime

from sqlalchemy import Column, DateTime


class TimestampMixin:
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mark rows as deleted with deleted_at instead of issuing SQL DELETE."""

    deleted_at = Column(DateTime, nullable=True, index=True)
