"""Tests for Baseline Snapshot Summary API endpoint."""
import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.api.routes.baseline_logs import create_baseline_cost_elements_for_baseline_log
from app.core.config import settings
from app.main import app
from app.models import (
    WBE,
    BaselineLog,
    BaselineLogCreate,
    CostElement,
    CostElementCreate,
    CostElementType,
    CostElementTypeCreate,
    Department,
    DepartmentCreate,
    Project,
    ProjectCreate,
    UserCreate,
    WBECreate,
)

client = TestClient(app)


def test_get_baseline_snapshot_summary(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting baseline snapshot summary with aggregated values."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Snapshot Summary Test Project",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
        status="active",
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create a WBE
    wbe_in = WBECreate(
        machine_type="Test Machine",
        project_id=project.project_id,
        revenue_allocation=Decimal("50000.00"),
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    # Create Department and CostElementType
    dept_code = f"DEPT_{uuid.uuid4().hex[:8]}"
    dept_in = DepartmentCreate(
        department_code=dept_code,
        department_name="Test Department",
    )
    dept = Department.model_validate(dept_in)
    db.add(dept)
    db.commit()
    db.refresh(dept)

    type_code = f"TYPE_{uuid.uuid4().hex[:8]}"
    cost_element_type_in = CostElementTypeCreate(
        type_code=type_code,
        type_name="Test Type",
        category_type="labor",
        department_id=dept.department_id,
    )
    cost_element_type = CostElementType.model_validate(cost_element_type_in)
    db.add(cost_element_type)
    db.commit()
    db.refresh(cost_element_type)

    # Create cost elements
    ce1_in = CostElementCreate(
        wbe_id=wbe.wbe_id,
        department_code=dept_code,
        department_name="Test Department",
        budget_bac=Decimal("10000.00"),
        revenue_plan=Decimal("12000.00"),
        cost_element_type_id=cost_element_type.cost_element_type_id,
    )
    ce1 = CostElement.model_validate(ce1_in)
    db.add(ce1)
    db.commit()
    db.refresh(ce1)

    ce2_in = CostElementCreate(
        wbe_id=wbe.wbe_id,
        department_code=dept_code,
        department_name="Test Department",
        budget_bac=Decimal("20000.00"),
        revenue_plan=Decimal("25000.00"),
        cost_element_type_id=cost_element_type.cost_element_type_id,
    )
    ce2 = CostElement.model_validate(ce2_in)
    db.add(ce2)
    db.commit()
    db.refresh(ce2)

    # Create baseline log
    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="Test baseline",
        project_id=project.project_id,
        created_by_id=user.id,
    )
    baseline = BaselineLog.model_validate(baseline_in)
    db.add(baseline)
    db.commit()
    db.refresh(baseline)

    # Create baseline cost elements (this will create BaselineCostElement records, NO BaselineSnapshot)
    create_baseline_cost_elements_for_baseline_log(
        session=db, baseline_log=baseline, created_by_id=user.id
    )
    db.commit()
    db.refresh(baseline)

    # Get snapshot summary via API (works without BaselineSnapshot)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline.baseline_id}/snapshot",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()

    # Verify response structure (uses BaselineLog data, snapshot_id = baseline_id for backward compatibility)
    assert content["snapshot_id"] == str(
        baseline.baseline_id
    )  # Uses baseline_id as snapshot_id
    assert content["baseline_id"] == str(baseline.baseline_id)
    assert content["baseline_date"] == "2024-01-15"
    assert content["milestone_type"] == "kickoff"
    assert content["description"] == "Test baseline"
    assert content["cost_element_count"] == 2

    # Verify aggregated values
    assert Decimal(content["total_budget_bac"]) == Decimal("30000.00")
    assert Decimal(content["total_revenue_plan"]) == Decimal("37000.00")
    # actual_ac from snapshotting should be "0.00" (no cost registrations)
    # The snapshotting function sets actual_ac = Decimal("0.00") when no registrations
    assert content["total_actual_ac"] == "0.00"
    assert Decimal(content["total_actual_ac"]) == Decimal("0.00")
    assert content["total_forecast_eac"] is None  # No forecasts
    assert content["total_earned_ev"] is None  # No earned value entries


def test_get_baseline_snapshot_summary_with_nulls(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test snapshot summary with NULL values in actual_ac, forecast_eac, earned_ev."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Snapshot NULL Test Project",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
        status="active",
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create a WBE
    wbe_in = WBECreate(
        machine_type="Test Machine",
        project_id=project.project_id,
        revenue_allocation=Decimal("50000.00"),
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    # Create Department and CostElementType
    dept_code = f"DEPT_{uuid.uuid4().hex[:8]}"
    dept_in = DepartmentCreate(
        department_code=dept_code,
        department_name="Test Department",
    )
    dept = Department.model_validate(dept_in)
    db.add(dept)
    db.commit()
    db.refresh(dept)

    type_code = f"TYPE_{uuid.uuid4().hex[:8]}"
    cost_element_type_in = CostElementTypeCreate(
        type_code=type_code,
        type_name="Test Type",
        category_type="labor",
        department_id=dept.department_id,
    )
    cost_element_type = CostElementType.model_validate(cost_element_type_in)
    db.add(cost_element_type)
    db.commit()
    db.refresh(cost_element_type)

    # Create cost element
    ce_in = CostElementCreate(
        wbe_id=wbe.wbe_id,
        department_code=dept_code,
        department_name="Test Department",
        budget_bac=Decimal("10000.00"),
        revenue_plan=Decimal("12000.00"),
        cost_element_type_id=cost_element_type.cost_element_type_id,
    )
    ce = CostElement.model_validate(ce_in)
    db.add(ce)
    db.commit()
    db.refresh(ce)

    # Create baseline log
    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="Test baseline",
        project_id=project.project_id,
        created_by_id=user.id,
    )
    baseline = BaselineLog.model_validate(baseline_in)
    db.add(baseline)
    db.commit()
    db.refresh(baseline)

    # Create baseline cost elements (NO BaselineSnapshot)
    create_baseline_cost_elements_for_baseline_log(
        session=db, baseline_log=baseline, created_by_id=user.id
    )
    db.commit()
    db.refresh(baseline)

    # Get snapshot summary via API (works without BaselineSnapshot)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline.baseline_id}/snapshot",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()

    # Verify NULL values are handled correctly
    # actual_ac from snapshotting should be "0.00" (no cost registrations)
    assert content["total_actual_ac"] == "0.00"
    assert Decimal(content["total_actual_ac"]) == Decimal("0.00")
    assert content["total_forecast_eac"] is None  # No forecasts
    assert content["total_earned_ev"] is None  # No earned value entries


def test_get_baseline_snapshot_summary_baseline_not_found(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test snapshot summary when baseline not found."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Not Found Test Project",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
        status="active",
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Try to get snapshot for non-existent baseline
    fake_baseline_id = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{fake_baseline_id}/snapshot",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert "Baseline log not found" in response.json()["detail"]


def test_get_baseline_snapshot_summary_project_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test snapshot summary when project not found."""
    fake_project_id = uuid.uuid4()
    fake_baseline_id = uuid.uuid4()

    response = client.get(
        f"{settings.API_V1_STR}/projects/{fake_project_id}/baseline-logs/{fake_baseline_id}/snapshot",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert "Project not found" in response.json()["detail"]


def test_get_baseline_snapshot_summary_wrong_project(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test snapshot summary when baseline belongs to different project."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create project 1
    project1_in = ProjectCreate(
        project_name="Project 1",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
        status="active",
    )
    project1 = Project.model_validate(project1_in)
    db.add(project1)
    db.commit()
    db.refresh(project1)

    # Create baseline for project 1
    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="Test baseline",
        project_id=project1.project_id,
        created_by_id=user.id,
    )
    baseline = BaselineLog.model_validate(baseline_in)
    db.add(baseline)
    db.commit()
    db.refresh(baseline)

    # Create project 2
    project2_in = ProjectCreate(
        project_name="Project 2",
        customer_name="Test Customer",
        contract_value=Decimal("200000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
        status="active",
    )
    project2 = Project.model_validate(project2_in)
    db.add(project2)
    db.commit()
    db.refresh(project2)

    # Try to get snapshot for baseline from project 1 using project 2's ID
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project2.project_id}/baseline-logs/{baseline.baseline_id}/snapshot",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert "Baseline log not found" in response.json()["detail"]


def test_get_baseline_snapshot_summary_no_snapshot(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test snapshot summary when snapshot doesn't exist (baseline exists but no snapshot)."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="No Snapshot Test Project",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
        status="active",
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create baseline log (but don't create snapshot)
    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="Test baseline",
        project_id=project.project_id,
        created_by_id=user.id,
    )
    baseline = BaselineLog.model_validate(baseline_in)
    db.add(baseline)
    db.commit()
    db.refresh(baseline)

    # Try to get snapshot summary
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline.baseline_id}/snapshot",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["baseline_id"] == str(baseline.baseline_id)
    assert content["cost_element_count"] == 0
