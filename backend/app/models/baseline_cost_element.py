"""Baseline Cost Element model and related schemas."""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, Column, DateTime
from sqlmodel import Field, Relationship, SQLModel

from app.models.baseline_log import BaselineLog
from app.models.cost_element import CostElement


class BaselineCostElementBase(SQLModel):
    """Base baseline cost element schema with common fields."""

    budget_bac: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(DECIMAL(15, 2), nullable=False)
    )
    revenue_plan: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(DECIMAL(15, 2), nullable=False)
    )
    actual_ac: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )
    forecast_eac: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )
    earned_ev: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )
    percent_complete: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(5, 2), nullable=True)
    )


class BaselineCostElementCreate(BaselineCostElementBase):
    """Schema for creating a new baseline cost element."""

    baseline_id: uuid.UUID
    cost_element_id: uuid.UUID


class BaselineCostElementUpdate(SQLModel):
    """Schema for updating a baseline cost element."""

    budget_bac: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )
    revenue_plan: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )
    actual_ac: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )
    forecast_eac: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )
    earned_ev: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )
    percent_complete: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(5, 2), nullable=True)
    )


class BaselineCostElement(BaselineCostElementBase, table=True):
    """Baseline Cost Element database model."""

    baseline_cost_element_id: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True
    )
    baseline_id: uuid.UUID = Field(
        foreign_key="baselinelog.baseline_id", nullable=False
    )
    cost_element_id: uuid.UUID = Field(
        foreign_key="costelement.cost_element_id", nullable=False
    )

    # Relationships
    baseline_log: BaselineLog | None = Relationship()
    cost_element: CostElement | None = Relationship()

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class BaselineCostElementPublic(BaselineCostElementBase):
    """Public baseline cost element schema for API responses."""

    baseline_cost_element_id: uuid.UUID
    baseline_id: uuid.UUID
    cost_element_id: uuid.UUID
    created_at: datetime


class BaselineCostElementWithCostElementPublic(BaselineCostElementPublic):
    """Public baseline cost element schema with CostElement fields for API responses."""

    department_code: str = Field(max_length=50)
    department_name: str = Field(max_length=100)
    cost_element_type_id: uuid.UUID
    wbe_id: uuid.UUID
    wbe_machine_type: str = Field(max_length=100)


class WBEWithBaselineCostElementsPublic(SQLModel):
    """Public WBE schema with baseline cost elements and aggregated totals."""

    wbe_id: uuid.UUID
    machine_type: str = Field(max_length=100)
    serial_number: str | None = Field(default=None, max_length=100)
    cost_elements: list[BaselineCostElementWithCostElementPublic] = Field(
        default_factory=list
    )
    wbe_total_budget_bac: Decimal = Field(
        sa_column=Column(DECIMAL(15, 2), nullable=False)
    )
    wbe_total_revenue_plan: Decimal = Field(
        sa_column=Column(DECIMAL(15, 2), nullable=False)
    )
    wbe_total_actual_ac: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )
    wbe_total_forecast_eac: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )
    wbe_total_earned_ev: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )


class BaselineCostElementsByWBEPublic(SQLModel):
    """Public schema for baseline cost elements grouped by WBE."""

    baseline_id: uuid.UUID
    wbes: list[WBEWithBaselineCostElementsPublic] = Field(default_factory=list)


class BaselineCostElementsPublic(SQLModel):
    """Public schema for paginated list of baseline cost elements."""

    data: list[BaselineCostElementWithCostElementPublic] = Field(default_factory=list)
    count: int = Field(default=0, ge=0)
