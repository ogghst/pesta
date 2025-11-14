"""Planned value calculation helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from math import erf, sqrt

from app.models import CostElement, CostElementSchedule

TWO_PLACES = Decimal("0.01")
FOUR_PLACES = Decimal("0.0001")
ONE = Decimal("1.0")
ZERO = Decimal("0.0")


class PlannedValueError(Exception):
    """Raised when attempting to calculate planned value for invalid inputs."""


def _quantize(value: Decimal, exp: Decimal) -> Decimal:
    return value.quantize(exp, rounding=ROUND_HALF_UP)


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(value, upper))


def _normal_cdf(x: float, mean: float, std_dev: float) -> float:
    return 0.5 * (1 + erf((x - mean) / (std_dev * sqrt(2))))


def calculate_planned_percent_complete(
    start_date: date,
    end_date: date,
    control_date: date,
    progression_type: str,
) -> Decimal:
    """Calculate the planned percent complete between start and end dates."""
    if end_date <= start_date:
        return ONE if control_date >= end_date else ZERO

    total_days = (end_date - start_date).days
    days_elapsed = (control_date - start_date).days
    normalized = _clamp(days_elapsed / total_days)

    progression = progression_type.lower()

    if progression == "linear":
        percent = normalized
    elif progression == "logarithmic":
        percent = normalized**2
    elif progression == "gaussian":
        mean = 0.5
        std_dev = 0.25
        cumulative = _normal_cdf(normalized, mean, std_dev)
        max_cdf = _normal_cdf(1.0, mean, std_dev)
        percent = cumulative / max_cdf if max_cdf else 1.0
    else:
        percent = normalized

    decimal_percent = Decimal(f"{_clamp(percent):.8f}")
    return _quantize(decimal_percent, FOUR_PLACES)


def calculate_planned_value(
    budget_bac: Decimal,
    start_date: date,
    end_date: date,
    control_date: date,
    progression_type: str,
) -> Decimal:
    """Calculate planned value as BAC multiplied by percent complete."""
    percent_complete = calculate_planned_percent_complete(
        start_date=start_date,
        end_date=end_date,
        control_date=control_date,
        progression_type=progression_type,
    )
    planned_value = budget_bac * percent_complete
    return _quantize(planned_value, TWO_PLACES)


def calculate_cost_element_planned_value(
    *,
    cost_element: CostElement,
    schedule: CostElementSchedule | None,
    control_date: date,
) -> tuple[Decimal, Decimal]:
    """Calculate planned value and percent for a cost element."""
    budget_bac = cost_element.budget_bac or Decimal("0.00")
    if schedule is None:
        return Decimal("0.00"), Decimal("0.0000")

    planned_value = calculate_planned_value(
        budget_bac=budget_bac,
        start_date=schedule.start_date,
        end_date=schedule.end_date,
        control_date=control_date,
        progression_type=schedule.progression_type,
    )
    percent = calculate_planned_percent_complete(
        start_date=schedule.start_date,
        end_date=schedule.end_date,
        control_date=control_date,
        progression_type=schedule.progression_type,
    )
    return planned_value, percent


@dataclass(slots=True)
class AggregateResult:
    planned_value: Decimal
    percent_complete: Decimal
    budget_bac: Decimal


def aggregate_planned_value(
    values: Iterable[tuple[Decimal, Decimal]],
) -> AggregateResult:
    """Aggregate planned values over multiple cost elements."""
    total_bac = Decimal("0.00")
    total_planned_value = Decimal("0.00")

    for planned_value, budget_bac in values:
        total_planned_value += planned_value
        total_bac += budget_bac

    if total_bac == Decimal("0.00"):
        return AggregateResult(
            planned_value=_quantize(total_planned_value, TWO_PLACES),
            percent_complete=Decimal("0.0000"),
            budget_bac=Decimal("0.00"),
        )

    percent_complete = total_planned_value / total_bac
    return AggregateResult(
        planned_value=_quantize(total_planned_value, TWO_PLACES),
        percent_complete=_quantize(percent_complete, FOUR_PLACES),
        budget_bac=_quantize(total_bac, TWO_PLACES),
    )
