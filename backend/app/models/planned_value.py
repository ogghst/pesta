"""Planned value response models."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import DECIMAL, Column, Date
from sqlmodel import Field, SQLModel


class PlannedValueBase(SQLModel):
    """Base schema for planned value responses."""

    level: str = Field(max_length=20)
    control_date: date = Field(sa_column=Column(Date, nullable=False))
    planned_value: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(DECIMAL(15, 2), nullable=False)
    )
    percent_complete: Decimal = Field(
        default=Decimal("0.0000"), sa_column=Column(DECIMAL(7, 4), nullable=False)
    )
    budget_bac: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(DECIMAL(15, 2), nullable=False)
    )


class PlannedValueCostElementPublic(PlannedValueBase):
    """Planned value response for cost elements."""

    cost_element_id: uuid.UUID = Field(nullable=False)


class PlannedValueWBEPublic(PlannedValueBase):
    """Planned value response for WBEs."""

    wbe_id: uuid.UUID = Field(nullable=False)


class PlannedValueProjectPublic(PlannedValueBase):
    """Planned value response for projects."""

    project_id: uuid.UUID = Field(nullable=False)
