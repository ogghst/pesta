"""Baseline Snapshot model and related schemas.

.. deprecated:: PLA-1
    This model is deprecated. Use :class:`BaselineLog` instead.
    The `department` and `is_pmb` fields have been merged into BaselineLog.
    New baselines should use BaselineLog directly.
    This model is kept for backward compatibility and will be removed in a future release.
"""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, Column, Date, DateTime
from sqlmodel import Field, Relationship, SQLModel

from app.models.baseline_log import BaselineLog
from app.models.project import Project

# Import for forward references
from app.models.user import User


class BaselineSnapshotBase(SQLModel):
    """Base baseline snapshot schema with common fields.

    .. deprecated:: PLA-1
        Use :class:`BaselineLog` instead. This schema is kept for backward compatibility.
    """

    baseline_date: date = Field(sa_column=Column(Date, nullable=False))
    milestone_type: str = Field(
        max_length=100
    )  # Will be validated as enum in application logic
    description: str | None = Field(default=None)
    department: str | None = Field(default=None, max_length=100)
    is_pmb: bool = Field(default=False)


class BaselineSnapshotCreate(BaselineSnapshotBase):
    """Schema for creating a new baseline snapshot."""

    project_id: uuid.UUID
    created_by_id: uuid.UUID


class BaselineSnapshotUpdate(SQLModel):
    """Schema for updating a baseline snapshot."""

    baseline_date: date | None = None
    milestone_type: str | None = Field(default=None, max_length=100)
    description: str | None = None
    department: str | None = Field(default=None, max_length=100)
    is_pmb: bool | None = None


class BaselineSnapshot(BaselineSnapshotBase, table=True):
    """Baseline Snapshot database model.

    .. deprecated:: PLA-1
        This model is deprecated. Use :class:`BaselineLog` instead.
        The `department` and `is_pmb` fields have been merged into BaselineLog.
        New baselines should use BaselineLog directly.
        This model is kept for backward compatibility and will be removed in a future release.

        TODO: Remove this model in next major version release.
        TODO: Create migration to drop BaselineSnapshot table (future).
    """

    snapshot_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="project.project_id", nullable=False)
    created_by_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    baseline_id: uuid.UUID | None = Field(
        foreign_key="baselinelog.baseline_id", nullable=True, default=None
    )

    # Relationships
    project: Project | None = Relationship()
    created_by: User | None = Relationship()
    baseline_log: BaselineLog | None = Relationship()

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class BaselineSnapshotPublic(BaselineSnapshotBase):
    """Public baseline snapshot schema for API responses."""

    snapshot_id: uuid.UUID
    project_id: uuid.UUID
    created_by_id: uuid.UUID
    baseline_id: uuid.UUID | None = None
    created_at: datetime


class BaselineSnapshotSummaryPublic(SQLModel):
    """Public schema for baseline snapshot summary with aggregated values."""

    snapshot_id: uuid.UUID
    baseline_id: uuid.UUID
    baseline_date: date
    milestone_type: str
    description: str | None = None
    total_budget_bac: Decimal = Field(sa_column=Column(DECIMAL(15, 2), nullable=False))
    total_revenue_plan: Decimal = Field(
        sa_column=Column(DECIMAL(15, 2), nullable=False)
    )
    total_actual_ac: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )
    total_forecast_eac: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )
    total_earned_ev: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )
    cost_element_count: int = Field(default=0, ge=0)
