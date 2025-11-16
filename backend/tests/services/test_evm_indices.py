"""Unit tests for EVM performance indices calculation helpers."""

from decimal import Decimal

from app.services.evm_indices import (
    aggregate_evm_indices,
    calculate_cpi,
    calculate_spi,
    calculate_tcpi,
)


def test_calculate_cpi_normal_case() -> None:
    """CPI should calculate correctly for normal case: EV=100, AC=80 → CPI=1.25."""
    ev = Decimal("100.00")
    ac = Decimal("80.00")

    result = calculate_cpi(ev, ac)

    assert result == Decimal("1.2500")


def test_calculate_cpi_undefined_ac_zero_ev_positive() -> None:
    """CPI should be undefined (None) when AC=0 and EV>0."""
    ev = Decimal("50.00")
    ac = Decimal("0.00")

    result = calculate_cpi(ev, ac)

    assert result is None


def test_calculate_cpi_undefined_ac_zero_ev_zero() -> None:
    """CPI should be undefined (None) when AC=0 and EV=0."""
    ev = Decimal("0.00")
    ac = Decimal("0.00")

    result = calculate_cpi(ev, ac)

    assert result is None


def test_calculate_cpi_quantization() -> None:
    """CPI should be quantized to 4 decimal places."""
    ev = Decimal("100.00")
    ac = Decimal("3.00")

    result = calculate_cpi(ev, ac)

    # Should be 33.3333... quantized to 4 places
    assert result == Decimal("33.3333")
    # Verify it's exactly 4 decimal places
    assert str(result).split(".")[1] == "3333"


def test_calculate_cpi_negative_values() -> None:
    """CPI should handle negative values appropriately."""
    ev = Decimal("-100.00")
    ac = Decimal("-80.00")

    result = calculate_cpi(ev, ac)

    # Negative divided by negative = positive
    assert result == Decimal("1.2500")


def test_calculate_spi_normal_case() -> None:
    """SPI should calculate correctly for normal case: EV=80, PV=100 → SPI=0.80."""
    ev = Decimal("80.00")
    pv = Decimal("100.00")

    result = calculate_spi(ev, pv)

    assert result == Decimal("0.8000")


def test_calculate_spi_null_pv_zero() -> None:
    """SPI should be null (None) when PV=0."""
    ev = Decimal("50.00")
    pv = Decimal("0.00")

    result = calculate_spi(ev, pv)

    assert result is None


def test_calculate_spi_quantization() -> None:
    """SPI should be quantized to 4 decimal places."""
    ev = Decimal("100.00")
    pv = Decimal("3.00")

    result = calculate_spi(ev, pv)

    # Should be 33.3333... quantized to 4 places
    assert result == Decimal("33.3333")
    # Verify it's exactly 4 decimal places
    assert str(result).split(".")[1] == "3333"


def test_calculate_spi_negative_values() -> None:
    """SPI should handle negative values appropriately."""
    ev = Decimal("-80.00")
    pv = Decimal("-100.00")

    result = calculate_spi(ev, pv)

    # Negative divided by negative = positive
    assert result == Decimal("0.8000")


def test_calculate_tcpi_normal_case() -> None:
    """TCPI should calculate correctly: BAC=1000, EV=600, AC=800 → TCPI=2.0."""
    bac = Decimal("1000.00")
    ev = Decimal("600.00")
    ac = Decimal("800.00")

    result = calculate_tcpi(bac, ev, ac)

    # TCPI = (BAC - EV) / (BAC - AC) = (1000 - 600) / (1000 - 800) = 400 / 200 = 2.0
    assert result == Decimal("2.0000")


def test_calculate_tcpi_overrun_bac_equals_ac() -> None:
    """TCPI should return 'overrun' when BAC=AC."""
    bac = Decimal("1000.00")
    ev = Decimal("600.00")
    ac = Decimal("1000.00")

    result = calculate_tcpi(bac, ev, ac)

    assert result == "overrun"


def test_calculate_tcpi_overrun_bac_less_than_ac() -> None:
    """TCPI should return 'overrun' when BAC<AC."""
    bac = Decimal("800.00")
    ev = Decimal("600.00")
    ac = Decimal("1000.00")

    result = calculate_tcpi(bac, ev, ac)

    assert result == "overrun"


def test_calculate_tcpi_undefined_bac_ac_zero() -> None:
    """TCPI should be undefined (None) when BAC=0 and AC=0."""
    bac = Decimal("0.00")
    ev = Decimal("0.00")
    ac = Decimal("0.00")

    result = calculate_tcpi(bac, ev, ac)

    assert result is None


def test_calculate_tcpi_quantization() -> None:
    """TCPI should be quantized to 4 decimal places."""
    bac = Decimal("1000.00")
    ev = Decimal("500.00")
    ac = Decimal("400.00")

    result = calculate_tcpi(bac, ev, ac)

    # TCPI = (1000 - 500) / (1000 - 400) = 500 / 600 = 0.8333...
    assert result == Decimal("0.8333")
    # Verify it's exactly 4 decimal places
    assert str(result).split(".")[1] == "8333"


def test_calculate_tcpi_negative_values() -> None:
    """TCPI should handle negative values appropriately."""
    bac = Decimal("1000.00")
    ev = Decimal("-100.00")
    ac = Decimal("200.00")

    result = calculate_tcpi(bac, ev, ac)

    # TCPI = (1000 - (-100)) / (1000 - 200) = 1100 / 800 = 1.3750
    assert result == Decimal("1.3750")


def test_aggregate_evm_indices_multiple_elements() -> None:
    """Aggregation should sum PV, EV, AC, BAC across multiple elements."""
    values = [
        (
            Decimal("100.00"),
            Decimal("80.00"),
            Decimal("90.00"),
            Decimal("200.00"),
        ),  # PV, EV, AC, BAC
        (Decimal("150.00"), Decimal("120.00"), Decimal("110.00"), Decimal("300.00")),
    ]

    result = aggregate_evm_indices(values)

    assert result.planned_value == Decimal("250.00")
    assert result.earned_value == Decimal("200.00")
    assert result.actual_cost == Decimal("200.00")
    assert result.budget_bac == Decimal("500.00")


def test_aggregate_evm_indices_empty() -> None:
    """Aggregation should return zeros for empty input."""
    values: list[tuple[Decimal, Decimal, Decimal, Decimal]] = []

    result = aggregate_evm_indices(values)

    assert result.planned_value == Decimal("0.00")
    assert result.earned_value == Decimal("0.00")
    assert result.actual_cost == Decimal("0.00")
    assert result.budget_bac == Decimal("0.00")


def test_aggregate_evm_indices_single_element() -> None:
    """Aggregation should work correctly for single element."""
    values = [
        (Decimal("100.00"), Decimal("80.00"), Decimal("90.00"), Decimal("200.00")),
    ]

    result = aggregate_evm_indices(values)

    assert result.planned_value == Decimal("100.00")
    assert result.earned_value == Decimal("80.00")
    assert result.actual_cost == Decimal("90.00")
    assert result.budget_bac == Decimal("200.00")


def test_aggregate_evm_indices_quantization() -> None:
    """Aggregation should quantize values correctly."""
    values = [
        (
            Decimal("100.123456"),
            Decimal("80.123456"),
            Decimal("90.123456"),
            Decimal("200.123456"),
        ),
    ]

    result = aggregate_evm_indices(values)

    # Should be quantized to 2 decimal places
    assert result.planned_value == Decimal("100.12")
    assert result.earned_value == Decimal("80.12")
    assert result.actual_cost == Decimal("90.12")
    assert result.budget_bac == Decimal("200.12")
