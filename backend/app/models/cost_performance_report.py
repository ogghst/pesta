"""Cost Performance Report response models."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import DECIMAL, Column, Date
from sqlmodel import Field, SQLModel

from app.models.evm_indices import EVMIndicesProjectPublic


class CostPerformanceReportRowPublic(SQLModel):
    """A single row in the cost performance report representing a cost element."""

    cost_element_id: uuid.UUID = Field(nullable=False)
    wbe_id: uuid.UUID = Field(nullable=False)
    wbe_name: str = Field(max_length=200, description="WBE machine_type")
    wbe_serial_number: str | None = Field(
        default=None, max_length=100, description="WBE serial_number"
    )
    department_code: str = Field(max_length=50)
    department_name: str = Field(max_length=200)
    cost_element_type_id: uuid.UUID | None = Field(default=None, nullable=True)
    cost_element_type_name: str | None = Field(
        default=None, max_length=200, description="Cost element type name"
    )
    # EVM metrics
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
    cpi: Decimal | None = Field(
        default=None,
        sa_column=Column(DECIMAL(7, 4), nullable=True),
        description="Cost Performance Index (CPI) = EV / AC. None when AC = 0.",
    )
    spi: Decimal | None = Field(
        default=None,
        sa_column=Column(DECIMAL(7, 4), nullable=True),
        description="Schedule Performance Index (SPI) = EV / PV. None when PV = 0.",
    )
    tcpi: Decimal | str | None = Field(
        default=None,
        description="To-Complete Performance Index (TCPI) = (BAC - EV) / (BAC - AC). Returns 'overrun' when BAC ≤ AC.",
    )
    cost_variance: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(DECIMAL(15, 2), nullable=False),
        description="Cost Variance (CV) = EV - AC. Negative = over-budget, positive = under-budget, zero = on-budget.",
    )
    schedule_variance: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(DECIMAL(15, 2), nullable=False),
        description="Schedule Variance (SV) = EV - PV. Negative = behind-schedule, positive = ahead-of-schedule, zero = on-schedule.",
    )


class CostPerformanceReportPublic(SQLModel):
    """Cost Performance Report response containing all rows and project summary."""

    project_id: uuid.UUID = Field(nullable=False)
    project_name: str = Field(max_length=200)
    control_date: date = Field(sa_column=Column(Date, nullable=False))
    rows: list[CostPerformanceReportRowPublic] = Field(default_factory=list)
    summary: EVMIndicesProjectPublic = Field(
        description="Aggregated project totals (EVM metrics)"
    )
