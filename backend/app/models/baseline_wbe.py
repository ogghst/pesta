"""Baseline WBE model and related schemas."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from sqlalchemy import DECIMAL, Column, DateTime
from sqlmodel import Field, Relationship, SQLModel

from app.models.baseline_log import BaselineLog
from app.models.version_status_mixin import VersionStatusMixin
from app.models.wbe import WBE


class BaselineWBEBase(SQLModel):
    """Base baseline WBE schema with EVM metrics."""

    planned_value: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(DECIMAL(15, 2), nullable=False)
    )
    earned_value: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(DECIMAL(15, 2), nullable=False)
    )
    actual_cost: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(DECIMAL(15, 2), nullable=False)
    )
    budget_bac: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(DECIMAL(15, 2), nullable=False)
    )
    eac: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(DECIMAL(15, 2), nullable=False)
    )
    forecasted_quality: Decimal = Field(
        default=Decimal("0.0000"), sa_column=Column(DECIMAL(8, 4), nullable=False)
    )
    cpi: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(10, 4), nullable=True)
    )
    spi: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(10, 4), nullable=True)
    )
    tcpi: Decimal | Literal["overrun"] | None = Field(
        default=None, sa_column=Column(DECIMAL(10, 4), nullable=True)
    )
    cost_variance: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(DECIMAL(15, 2), nullable=False)
    )
    schedule_variance: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(DECIMAL(15, 2), nullable=False)
    )


class BaselineWBECreate(BaselineWBEBase):
    """Schema for creating a new baseline WBE."""

    baseline_id: uuid.UUID
    wbe_id: uuid.UUID


class BaselineWBEUpdate(SQLModel):
    """Schema for updating a baseline WBE."""

    planned_value: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )
    earned_value: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )
    actual_cost: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )
    budget_bac: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )
    eac: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )
    forecasted_quality: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(8, 4), nullable=True)
    )
    cpi: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(10, 4), nullable=True)
    )
    spi: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(10, 4), nullable=True)
    )
    tcpi: Decimal | Literal["overrun"] | None = Field(
        default=None, sa_column=Column(DECIMAL(10, 4), nullable=True)
    )
    cost_variance: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )
    schedule_variance: Decimal | None = Field(
        default=None, sa_column=Column(DECIMAL(15, 2), nullable=True)
    )


class BaselineWBE(BaselineWBEBase, VersionStatusMixin, table=True):
    """Baseline WBE database model."""

    baseline_wbe_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    baseline_id: uuid.UUID = Field(
        foreign_key="baselinelog.baseline_id", nullable=False
    )
    wbe_id: uuid.UUID = Field(foreign_key="wbe.wbe_id", nullable=False)

    # Relationships
    baseline_log: BaselineLog | None = Relationship()
    wbe: WBE | None = Relationship()

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class BaselineWBEPublic(BaselineWBEBase):
    """Public baseline WBE schema for API responses."""

    baseline_wbe_id: uuid.UUID
    baseline_id: uuid.UUID
    wbe_id: uuid.UUID
    created_at: datetime
    entity_id: uuid.UUID
    status: str
    version: int


class BaselineWBEPublicWithWBE(BaselineWBEPublic):
    """Public baseline WBE schema with WBE details for API responses."""

    wbe_machine_type: str | None = None
    wbe_serial_number: str | None = None
