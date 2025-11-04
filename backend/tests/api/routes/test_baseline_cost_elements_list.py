"""Tests for Baseline Cost Elements List API endpoint."""
import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.api.routes.baseline_logs import create_baseline_snapshot_for_baseline_log
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


def test_get_baseline_cost_elements_success(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting baseline cost elements as flat list."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="List Test Project",
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

    # Create WBE
    wbe_in = WBECreate(
        machine_type="Test Machine",
        project_id=project.project_id,
        revenue_allocation=Decimal("50000.00"),
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

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

    # Create snapshot (this will create BaselineCostElement records)
    create_baseline_snapshot_for_baseline_log(
        session=db, baseline_log=baseline, created_by_id=user.id
    )

    # Get cost elements list via API
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline.baseline_id}/cost-elements",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()

    # Verify response structure
    assert "data" in content
    assert "count" in content
    assert content["count"] == 2  # Should have 2 cost elements
    assert len(content["data"]) == 2

    # Verify cost element details
    ce1_data = next(
        ce
        for ce in content["data"]
        if ce["cost_element_id"] == str(ce1.cost_element_id)
    )
    assert ce1_data["department_code"] == dept_code
    assert ce1_data["department_name"] == "Test Department"
    assert Decimal(ce1_data["budget_bac"]) == Decimal("10000.00")
    assert Decimal(ce1_data["revenue_plan"]) == Decimal("12000.00")
    assert ce1_data["wbe_id"] == str(wbe.wbe_id)
    assert ce1_data["wbe_machine_type"] == "Test Machine"


def test_get_baseline_cost_elements_pagination(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test pagination for baseline cost elements list."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Pagination Test Project",
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

    # Create WBE
    wbe_in = WBECreate(
        machine_type="Test Machine",
        project_id=project.project_id,
        revenue_allocation=Decimal("50000.00"),
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    # Create 5 cost elements
    cost_elements = []
    for i in range(5):
        ce_in = CostElementCreate(
            wbe_id=wbe.wbe_id,
            department_code=dept_code,
            department_name="Test Department",
            budget_bac=Decimal(f"{(i+1)*10000}.00"),
            revenue_plan=Decimal(f"{(i+1)*12000}.00"),
            cost_element_type_id=cost_element_type.cost_element_type_id,
        )
        ce = CostElement.model_validate(ce_in)
        db.add(ce)
        db.commit()
        db.refresh(ce)
        cost_elements.append(ce)

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

    # Create snapshot
    create_baseline_snapshot_for_baseline_log(
        session=db, baseline_log=baseline, created_by_id=user.id
    )

    # Test first page (limit=2)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline.baseline_id}/cost-elements",
        params={"skip": 0, "limit": 2},
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["count"] == 5  # Total count should be 5
    assert len(content["data"]) == 2  # But only 2 items on this page

    # Test second page (skip=2, limit=2)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline.baseline_id}/cost-elements",
        params={"skip": 2, "limit": 2},
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["count"] == 5  # Total count should still be 5
    assert len(content["data"]) == 2  # 2 items on second page

    # Test third page (skip=4, limit=2)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline.baseline_id}/cost-elements",
        params={"skip": 4, "limit": 2},
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["count"] == 5  # Total count should still be 5
    assert len(content["data"]) == 1  # Only 1 item on third page


def test_get_baseline_cost_elements_empty(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting baseline cost elements when no cost elements exist."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Empty Test Project",
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

    # Create baseline log (but no cost elements)
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

    # Create snapshot (will create no BaselineCostElement records since no cost elements)
    create_baseline_snapshot_for_baseline_log(
        session=db, baseline_log=baseline, created_by_id=user.id
    )

    # Get cost elements list via API
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline.baseline_id}/cost-elements",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()

    # Verify empty response
    assert content["count"] == 0
    assert len(content["data"]) == 0


def test_get_baseline_cost_elements_baseline_not_found(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test cost elements list when baseline not found."""
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

    # Try to get cost elements for non-existent baseline
    fake_baseline_id = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{fake_baseline_id}/cost-elements",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert "Baseline log not found" in response.json()["detail"]


def test_get_baseline_cost_elements_project_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test cost elements list when project not found."""
    fake_project_id = uuid.uuid4()
    fake_baseline_id = uuid.uuid4()

    response = client.get(
        f"{settings.API_V1_STR}/projects/{fake_project_id}/baseline-logs/{fake_baseline_id}/cost-elements",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert "Project not found" in response.json()["detail"]


def test_get_baseline_cost_elements_wrong_project(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test cost elements list when baseline belongs to different project."""
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

    # Try to get cost elements for baseline from project 1 using project 2's ID
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project2.project_id}/baseline-logs/{baseline.baseline_id}/cost-elements",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert "Baseline log not found" in response.json()["detail"]
