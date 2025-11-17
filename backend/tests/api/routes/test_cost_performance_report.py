"""Tests for Cost Performance Report API routes."""

import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import (
    WBE,
    CostElement,
    CostElementCreate,
    CostElementType,
    CostElementTypeCreate,
    Project,
    ProjectCreate,
    UserCreate,
    WBECreate,
)
from tests.utils.cost_element_schedule import create_schedule_for_cost_element
from tests.utils.cost_registration import create_random_cost_registration
from tests.utils.earned_value_entry import create_earned_value_entry
from tests.utils.user import set_time_machine_date


def test_get_cost_performance_report(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting cost performance report for a project."""
    # Setup: Create project hierarchy
    from app import crud

    email = f"pm_{uuid.uuid4().hex[:8]}@example.com"
    user_in = UserCreate(email=email, password="testpassword123")
    pm_user = crud.create_user(session=db, user_create=user_in)

    project_in = ProjectCreate(
        project_name="Report Test Project",
        customer_name="Test Customer",
        contract_value=100000.00,
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=pm_user.id,
        status="active",
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Test Machine",
        serial_number="SN-001",
        revenue_allocation=50000.00,
        status="designing",
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    # Create cost element type
    cet_in = CostElementTypeCreate(
        type_code=f"test_eng_{uuid.uuid4().hex[:8]}",
        type_name="Test Engineering",
        category_type="engineering_mechanical",
        display_order=1,
        is_active=True,
    )
    cet = CostElementType.model_validate(cet_in)
    db.add(cet)
    db.commit()
    db.refresh(cet)

    # Create cost element
    ce_in = CostElementCreate(
        wbe_id=wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="ENG",
        department_name="Engineering",
        budget_bac=Decimal("10000.00"),
        revenue_plan=Decimal("12000.00"),
        status="active",
    )
    ce = CostElement.model_validate(ce_in)
    db.add(ce)
    db.commit()
    db.refresh(ce)

    # Create schedule
    create_schedule_for_cost_element(
        db,
        ce.cost_element_id,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        progression_type="linear",
        registration_date=date(2024, 1, 1),
    )

    # Create cost registration
    cr = create_random_cost_registration(
        db,
        cost_element_id=ce.cost_element_id,
        registration_date=date(2024, 6, 15),
        created_by_id=pm_user.id,
    )
    cr.amount = Decimal("5000.00")
    cr.cost_category = "labor"
    cr.description = "Test cost"
    db.add(cr)
    db.commit()
    db.refresh(cr)

    # Create earned value entry
    create_earned_value_entry(
        db,
        cost_element_id=ce.cost_element_id,
        completion_date=date(2024, 6, 15),
        percent_complete=Decimal("50.00"),
        description="50% complete",
        created_by_id=pm_user.id,
    )

    # Set control date in future to include all items
    control_date = date(2025, 12, 31)
    set_time_machine_date(client, superuser_token_headers, control_date)

    # Test: GET /projects/{project_id}/reports/cost-performance
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/reports/cost-performance",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["project_id"] == str(project.project_id)
    assert content["project_name"] == "Report Test Project"
    assert content["control_date"] == str(control_date)
    assert len(content["rows"]) == 1
    assert content["summary"]["project_id"] == str(project.project_id)
    assert content["summary"]["budget_bac"] == "10000.00"
    assert content["summary"]["actual_cost"] == "5000.00"
    assert content["summary"]["earned_value"] == "5000.00"


def test_get_cost_performance_report_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test getting cost performance report for non-existent project."""
    fake_project_id = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/projects/{fake_project_id}/reports/cost-performance",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert "not found" in content["detail"].lower()


def test_get_cost_performance_report_empty_project(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting cost performance report for project with no cost elements."""
    from app import crud

    email = f"pm_{uuid.uuid4().hex[:8]}@example.com"
    user_in = UserCreate(email=email, password="testpassword123")
    pm_user = crud.create_user(session=db, user_create=user_in)

    project_in = ProjectCreate(
        project_name="Empty Project",
        customer_name="Test Customer",
        contract_value=100000.00,
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=pm_user.id,
        status="active",
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    control_date = date(2025, 12, 31)
    set_time_machine_date(client, superuser_token_headers, control_date)

    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/reports/cost-performance",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["project_id"] == str(project.project_id)
    assert len(content["rows"]) == 0
    assert content["summary"]["budget_bac"] == "0.00"
    assert content["summary"]["actual_cost"] == "0.00"
    assert content["summary"]["earned_value"] == "0.00"
