"""Unit tests for planned value progression helpers."""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.services.planned_value import (
    calculate_planned_percent_complete,
    calculate_planned_value,
)


@pytest.mark.parametrize(
    "control_offset,expected_percent",
    [
        (0, Decimal("0.0")),
        (15, Decimal("0.5")),
        (30, Decimal("1.0")),
    ],
)
def test_linear_progression_percent(
    control_offset: int, expected_percent: Decimal
) -> None:
    """Linear progression should scale linearly between start and end dates."""
    start = date(2024, 1, 1)
    end = date(2024, 1, 31)
    control_date = start + timedelta(days=control_offset)

    percent_complete = calculate_planned_percent_complete(
        start_date=start,
        end_date=end,
        control_date=control_date,
        progression_type="linear",
    )

    assert percent_complete == expected_percent


def test_linear_progression_before_start_is_zero() -> None:
    """Control date before start date should clamp percent to zero."""
    start = date(2024, 1, 10)
    end = date(2024, 2, 10)
    control_date = start - timedelta(days=5)

    percent_complete = calculate_planned_percent_complete(
        start_date=start,
        end_date=end,
        control_date=control_date,
        progression_type="linear",
    )

    assert percent_complete == Decimal("0.0")


def test_linear_progression_after_end_is_one() -> None:
    """Control date after end date should clamp percent to one."""
    start = date(2024, 1, 10)
    end = date(2024, 2, 10)
    control_date = end + timedelta(days=5)

    percent_complete = calculate_planned_percent_complete(
        start_date=start,
        end_date=end,
        control_date=control_date,
        progression_type="linear",
    )

    assert percent_complete == Decimal("1.0")


def test_gaussian_progression_is_monotonic() -> None:
    """Gaussian progression should increase monotonically and peak near midpoint."""
    start = date(2024, 1, 1)
    end = date(2024, 1, 31)

    early = calculate_planned_percent_complete(start, end, start, "gaussian")
    mid = calculate_planned_percent_complete(
        start, end, start + timedelta(days=15), "gaussian"
    )
    late = calculate_planned_percent_complete(start, end, end, "gaussian")

    assert Decimal("0.0") <= early < mid < late <= Decimal("1.0")


def test_logarithmic_progression_curves_slow_start() -> None:
    """Logarithmic progression should start slow and accelerate toward the end."""
    start = date(2024, 1, 1)
    end = date(2024, 1, 31)

    quarter = calculate_planned_percent_complete(
        start, end, start + timedelta(days=8), "logarithmic"
    )
    half = calculate_planned_percent_complete(
        start, end, start + timedelta(days=16), "logarithmic"
    )
    near_end = calculate_planned_percent_complete(
        start, end, end - timedelta(days=1), "logarithmic"
    )

    assert Decimal("0.0") <= quarter < half < near_end <= Decimal("1.0")


def test_calculate_planned_value_uses_percent() -> None:
    """Planned value should equal BAC multiplied by percent complete."""
    start = date(2024, 1, 1)
    end = date(2024, 1, 31)
    control_date = start + timedelta(days=15)

    planned_value = calculate_planned_value(
        budget_bac=Decimal("100000"),
        start_date=start,
        end_date=end,
        control_date=control_date,
        progression_type="linear",
    )

    # 15 / 30 = 0.5 of the budget
    assert planned_value == Decimal("50000.00")
