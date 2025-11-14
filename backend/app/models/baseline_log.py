"""Baseline Log model and related schemas."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, Column, Date, DateTime
from sqlmodel import Field, Relationship, SQLModel

# Import for forward references
from app.models.project import Project
from app.models.user import User


class BaselineLogBase(SQLModel):
    """Base baseline log schema with common fields."""

    baseline_type: str = Field(
        max_length=50
    )  # Will be validated as enum in application logic
    baseline_date: date = Field(sa_column=Column(Date, nullable=False))
    milestone_type: str = Field(
        max_length=100
    )  # Will be validated as enum in application logic
    description: str | None = Field(default=None)
    is_cancelled: bool = Field(default=False)
    department: str | None = Field(default=None, max_length=100)
    is_pmb: bool = Field(default=False)


class BaselineLogCreate(BaselineLogBase):
    """Schema for creating a new baseline log entry."""

    project_id: uuid.UUID
    created_by_id: uuid.UUID


class BaselineLogUpdate(SQLModel):
    """Schema for updating a baseline log entry."""

    baseline_type: str | None = Field(default=None, max_length=50)
    baseline_date: date | None = None
    milestone_type: str | None = Field(default=None, max_length=100)
    description: str | None = None
    is_cancelled: bool | None = None
    department: str | None = Field(default=None, max_length=100)
    is_pmb: bool | None = None


class BaselineLog(BaselineLogBase, table=True):
    """Baseline Log database model."""

    baseline_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="project.project_id", nullable=False)
    created_by_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)

    # Relationships
    project: Project | None = Relationship()
    created_by: User | None = Relationship()

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class BaselineLogPublic(BaselineLogBase):
    """Public baseline log schema for API responses."""

    baseline_id: uuid.UUID
    project_id: uuid.UUID
    created_by_id: uuid.UUID
    created_at: datetime


class BaselineSummaryPublic(SQLModel):
    """Public schema for baseline summary with aggregated values."""

    snapshot_id: uuid.UUID
    baseline_id: uuid.UUID
    baseline_date: date
    milestone_type: str
    description: str | None = None
    total_budget_bac: Decimal = Field(sa_column=Column(DECIMAL(15, 2), nullable=False))
    total_revenue_plan: Decimal = Field(
        sa_column=Column(DECIMAL(15, 2), nullable=False)
    )
    total_planned_value: Decimal = Field(
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


# Backward-compatible alias retained for historical API contract
BaselineSnapshotSummaryPublic = BaselineSummaryPublic
