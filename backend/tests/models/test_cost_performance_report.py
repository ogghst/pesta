"""Tests for Cost Performance Report models."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.cost_performance_report import (
    CostPerformanceReportPublic,
    CostPerformanceReportRowPublic,
)
from app.models.evm_indices import EVMIndicesProjectPublic


def test_cost_performance_report_row_public_creation() -> None:
    """Test creating a CostPerformanceReportRowPublic with all required fields."""
    row = CostPerformanceReportRowPublic(
        cost_element_id=uuid.uuid4(),
        wbe_id=uuid.uuid4(),
        wbe_name="Test Machine",
        department_code="ENG",
        department_name="Engineering",
        planned_value=Decimal("10000.00"),
        earned_value=Decimal("8000.00"),
        actual_cost=Decimal("9000.00"),
        budget_bac=Decimal("10000.00"),
        cpi=Decimal("0.8889"),
        spi=Decimal("0.8000"),
        tcpi=Decimal("2.0000"),
        cost_variance=Decimal("-1000.00"),
        schedule_variance=Decimal("-2000.00"),
    )

    assert row.cost_element_id is not None
    assert row.wbe_id is not None
    assert row.wbe_name == "Test Machine"
    assert row.department_code == "ENG"
    assert row.planned_value == Decimal("10000.00")
    assert row.cpi == Decimal("0.8889")
    assert row.cost_variance == Decimal("-1000.00")


def test_cost_performance_report_row_public_optional_fields() -> None:
    """Test CostPerformanceReportRowPublic with optional fields."""
    row = CostPerformanceReportRowPublic(
        cost_element_id=uuid.uuid4(),
        wbe_id=uuid.uuid4(),
        wbe_name="Test Machine",
        wbe_serial_number="SN-001",
        department_code="ENG",
        department_name="Engineering",
        cost_element_type_id=uuid.uuid4(),
        cost_element_type_name="Engineering Type",
        planned_value=Decimal("10000.00"),
        earned_value=Decimal("8000.00"),
        actual_cost=Decimal("0.00"),
        budget_bac=Decimal("10000.00"),
        cpi=None,  # AC = 0, so CPI is None
        spi=Decimal("0.8000"),
        tcpi=None,
        cost_variance=Decimal("8000.00"),
        schedule_variance=Decimal("-2000.00"),
    )

    assert row.wbe_serial_number == "SN-001"
    assert row.cost_element_type_id is not None
    assert row.cost_element_type_name == "Engineering Type"
    assert row.cpi is None  # AC = 0


def test_cost_performance_report_row_public_tcpi_overrun() -> None:
    """Test CostPerformanceReportRowPublic with TCPI 'overrun' value."""
    row = CostPerformanceReportRowPublic(
        cost_element_id=uuid.uuid4(),
        wbe_id=uuid.uuid4(),
        wbe_name="Test Machine",
        department_code="ENG",
        department_name="Engineering",
        planned_value=Decimal("10000.00"),
        earned_value=Decimal("5000.00"),
        actual_cost=Decimal("12000.00"),  # AC > BAC
        budget_bac=Decimal("10000.00"),
        cpi=Decimal("0.4167"),
        spi=Decimal("0.5000"),
        tcpi="overrun",  # BAC <= AC
        cost_variance=Decimal("-7000.00"),
        schedule_variance=Decimal("-5000.00"),
    )

    assert row.tcpi == "overrun"


def test_cost_performance_report_public_creation() -> None:
    """Test creating a CostPerformanceReportPublic with rows and summary."""
    project_id = uuid.uuid4()
    control_date = date(2024, 6, 15)

    row1 = CostPerformanceReportRowPublic(
        cost_element_id=uuid.uuid4(),
        wbe_id=uuid.uuid4(),
        wbe_name="Machine A",
        department_code="ENG",
        department_name="Engineering",
        planned_value=Decimal("10000.00"),
        earned_value=Decimal("8000.00"),
        actual_cost=Decimal("9000.00"),
        budget_bac=Decimal("10000.00"),
        cpi=Decimal("0.8889"),
        spi=Decimal("0.8000"),
        tcpi=Decimal("2.0000"),
        cost_variance=Decimal("-1000.00"),
        schedule_variance=Decimal("-2000.00"),
    )

    summary = EVMIndicesProjectPublic(
        level="project",
        control_date=control_date,
        project_id=project_id,
        planned_value=Decimal("10000.00"),
        earned_value=Decimal("8000.00"),
        actual_cost=Decimal("9000.00"),
        budget_bac=Decimal("10000.00"),
        cpi=Decimal("0.8889"),
        spi=Decimal("0.8000"),
        tcpi=Decimal("2.0000"),
        cost_variance=Decimal("-1000.00"),
        schedule_variance=Decimal("-2000.00"),
    )

    report = CostPerformanceReportPublic(
        project_id=project_id,
        project_name="Test Project",
        control_date=control_date,
        rows=[row1],
        summary=summary,
    )

    assert report.project_id == project_id
    assert report.project_name == "Test Project"
    assert report.control_date == control_date
    assert len(report.rows) == 1
    assert report.summary.project_id == project_id


def test_cost_performance_report_public_empty_rows() -> None:
    """Test CostPerformanceReportPublic with empty rows list."""
    project_id = uuid.uuid4()
    control_date = date(2024, 6, 15)

    summary = EVMIndicesProjectPublic(
        level="project",
        control_date=control_date,
        project_id=project_id,
        planned_value=Decimal("0.00"),
        earned_value=Decimal("0.00"),
        actual_cost=Decimal("0.00"),
        budget_bac=Decimal("0.00"),
        cpi=None,
        spi=None,
        tcpi=None,
        cost_variance=Decimal("0.00"),
        schedule_variance=Decimal("0.00"),
    )

    report = CostPerformanceReportPublic(
        project_id=project_id,
        project_name="Empty Project",
        control_date=control_date,
        rows=[],
        summary=summary,
    )

    assert len(report.rows) == 0
    assert report.summary.budget_bac == Decimal("0.00")


def test_cost_performance_report_row_public_validation() -> None:
    """Test that CostPerformanceReportRowPublic validates required fields."""
    with pytest.raises(ValidationError):
        # Missing required field
        CostPerformanceReportRowPublic(
            cost_element_id=uuid.uuid4(),
            # Missing wbe_id
            wbe_name="Test Machine",
            department_code="ENG",
            department_name="Engineering",
            planned_value=Decimal("10000.00"),
            earned_value=Decimal("8000.00"),
            actual_cost=Decimal("9000.00"),
            budget_bac=Decimal("10000.00"),
            cpi=Decimal("0.8889"),
            spi=Decimal("0.8000"),
            tcpi=Decimal("2.0000"),
            cost_variance=Decimal("-1000.00"),
            schedule_variance=Decimal("-2000.00"),
        )


def test_cost_performance_report_row_public_serialization() -> None:
    """Test that CostPerformanceReportRowPublic can be serialized to dict/JSON."""
    row = CostPerformanceReportRowPublic(
        cost_element_id=uuid.uuid4(),
        wbe_id=uuid.uuid4(),
        wbe_name="Test Machine",
        department_code="ENG",
        department_name="Engineering",
        planned_value=Decimal("10000.00"),
        earned_value=Decimal("8000.00"),
        actual_cost=Decimal("9000.00"),
        budget_bac=Decimal("10000.00"),
        cpi=Decimal("0.8889"),
        spi=Decimal("0.8000"),
        tcpi=Decimal("2.0000"),
        cost_variance=Decimal("-1000.00"),
        schedule_variance=Decimal("-2000.00"),
    )

    # Test model_dump (Pydantic v2)
    data = row.model_dump()
    assert isinstance(data, dict)
    assert "cost_element_id" in data
    assert "wbe_name" in data
    assert "planned_value" in data

    # Test JSON serialization
    json_data = row.model_dump_json()
    assert isinstance(json_data, str)
    assert "Test Machine" in json_data
