"""Tests for Baseline Cost Elements by WBE API endpoint."""
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


def test_get_baseline_cost_elements_by_wbe_multiple_wbes(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting baseline cost elements grouped by WBE with multiple WBEs."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Multiple WBE Test Project",
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

    # Create WBE 1
    wbe1_in = WBECreate(
        machine_type="Machine Type A",
        project_id=project.project_id,
        revenue_allocation=Decimal("50000.00"),
    )
    wbe1 = WBE.model_validate(wbe1_in)
    db.add(wbe1)
    db.commit()
    db.refresh(wbe1)

    # Create WBE 2
    wbe2_in = WBECreate(
        machine_type="Machine Type B",
        serial_number="SN-002",
        project_id=project.project_id,
        revenue_allocation=Decimal("50000.00"),
    )
    wbe2 = WBE.model_validate(wbe2_in)
    db.add(wbe2)
    db.commit()
    db.refresh(wbe2)

    # Create cost elements for WBE 1
    ce1_in = CostElementCreate(
        wbe_id=wbe1.wbe_id,
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
        wbe_id=wbe1.wbe_id,
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

    # Create cost element for WBE 2
    ce3_in = CostElementCreate(
        wbe_id=wbe2.wbe_id,
        department_code=dept_code,
        department_name="Test Department",
        budget_bac=Decimal("15000.00"),
        revenue_plan=Decimal("18000.00"),
        cost_element_type_id=cost_element_type.cost_element_type_id,
    )
    ce3 = CostElement.model_validate(ce3_in)
    db.add(ce3)
    db.commit()
    db.refresh(ce3)

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
    create_baseline_cost_elements_for_baseline_log(
        session=db, baseline_log=baseline, created_by_id=user.id
    )

    # Get cost elements by WBE via API
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline.baseline_id}/cost-elements-by-wbe",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()

    # Verify response structure
    assert content["baseline_id"] == str(baseline.baseline_id)
    assert len(content["wbes"]) == 2  # Should have 2 WBEs

    # Find WBE 1 and WBE 2 in response
    wbe1_data = next(w for w in content["wbes"] if w["wbe_id"] == str(wbe1.wbe_id))
    wbe2_data = next(w for w in content["wbes"] if w["wbe_id"] == str(wbe2.wbe_id))

    # Verify WBE 1 data
    assert wbe1_data["machine_type"] == "Machine Type A"
    assert len(wbe1_data["cost_elements"]) == 2  # 2 cost elements
    assert Decimal(wbe1_data["wbe_total_budget_bac"]) == Decimal("30000.00")
    assert Decimal(wbe1_data["wbe_total_revenue_plan"]) == Decimal("37000.00")
    assert Decimal(wbe1_data["wbe_total_planned_value"]) == Decimal("0.00")

    # Verify WBE 2 data
    assert wbe2_data["machine_type"] == "Machine Type B"
    assert wbe2_data["serial_number"] == "SN-002"
    assert len(wbe2_data["cost_elements"]) == 1  # 1 cost element
    assert Decimal(wbe2_data["wbe_total_budget_bac"]) == Decimal("15000.00")
    assert Decimal(wbe2_data["wbe_total_revenue_plan"]) == Decimal("18000.00")
    assert Decimal(wbe2_data["wbe_total_planned_value"]) == Decimal("0.00")

    # Verify cost element details in WBE 1
    ce1_data = next(
        ce
        for ce in wbe1_data["cost_elements"]
        if ce["cost_element_id"] == str(ce1.cost_element_id)
    )
    assert ce1_data["department_code"] == dept_code
    assert ce1_data["department_name"] == "Test Department"
    assert Decimal(ce1_data["budget_bac"]) == Decimal("10000.00")
    assert Decimal(ce1_data["revenue_plan"]) == Decimal("12000.00")


def test_get_baseline_cost_elements_by_wbe_empty_cost_elements(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting baseline cost elements when WBE has no cost elements."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Empty Cost Elements Test Project",
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

    # Create WBE with no cost elements
    wbe_in = WBECreate(
        machine_type="Empty WBE",
        project_id=project.project_id,
        revenue_allocation=Decimal("50000.00"),
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

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

    # Create snapshot (will create no BaselineCostElement records since no cost elements)
    create_baseline_cost_elements_for_baseline_log(
        session=db, baseline_log=baseline, created_by_id=user.id
    )

    # Get cost elements by WBE via API
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline.baseline_id}/cost-elements-by-wbe",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()

    # Verify response structure
    assert content["baseline_id"] == str(baseline.baseline_id)
    assert len(content["wbes"]) == 1  # Should have 1 WBE

    # Verify WBE has empty cost elements list
    wbe_data = content["wbes"][0]
    assert wbe_data["wbe_id"] == str(wbe.wbe_id)
    assert wbe_data["machine_type"] == "Empty WBE"
    assert len(wbe_data["cost_elements"]) == 0  # No cost elements
    assert Decimal(wbe_data["wbe_total_budget_bac"]) == Decimal("0.00")
    assert Decimal(wbe_data["wbe_total_revenue_plan"]) == Decimal("0.00")
    assert Decimal(wbe_data["wbe_total_planned_value"]) == Decimal("0.00")
    assert wbe_data["wbe_total_actual_ac"] is None
    assert wbe_data["wbe_total_forecast_eac"] is None
    assert wbe_data["wbe_total_earned_ev"] is None


def test_get_baseline_cost_elements_by_wbe_aggregation_accuracy(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test that WBE totals accurately aggregate cost element values."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Aggregation Test Project",
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

    # Create multiple cost elements with known values
    cost_elements = []
    for i in range(3):
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
    create_baseline_cost_elements_for_baseline_log(
        session=db, baseline_log=baseline, created_by_id=user.id
    )

    # Get cost elements by WBE via API
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline.baseline_id}/cost-elements-by-wbe",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()

    # Find WBE in response
    wbe_data = content["wbes"][0]
    assert wbe_data["wbe_id"] == str(wbe.wbe_id)

    # Verify aggregation: 10000 + 20000 + 30000 = 60000
    expected_total_bac = Decimal("60000.00")
    assert Decimal(wbe_data["wbe_total_budget_bac"]) == expected_total_bac

    # Verify aggregation: 12000 + 24000 + 36000 = 72000
    expected_total_revenue = Decimal("72000.00")
    assert Decimal(wbe_data["wbe_total_revenue_plan"]) == expected_total_revenue
    assert Decimal(wbe_data["wbe_total_planned_value"]) == Decimal("0.00")

    # Verify individual cost elements sum to totals
    actual_sum_bac = sum(Decimal(ce["budget_bac"]) for ce in wbe_data["cost_elements"])
    assert actual_sum_bac == expected_total_bac

    actual_sum_revenue = sum(
        Decimal(ce["revenue_plan"]) for ce in wbe_data["cost_elements"]
    )
    assert actual_sum_revenue == expected_total_revenue


def test_get_baseline_cost_elements_by_wbe_baseline_not_found(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test cost elements by WBE when baseline not found."""
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
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{fake_baseline_id}/cost-elements-by-wbe",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert "Baseline log not found" in response.json()["detail"]


def test_get_baseline_cost_elements_by_wbe_project_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test cost elements by WBE when project not found."""
    fake_project_id = uuid.uuid4()
    fake_baseline_id = uuid.uuid4()

    response = client.get(
        f"{settings.API_V1_STR}/projects/{fake_project_id}/baseline-logs/{fake_baseline_id}/cost-elements-by-wbe",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert "Project not found" in response.json()["detail"]


def test_get_baseline_cost_elements_by_wbe_wrong_project(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test cost elements by WBE when baseline belongs to different project."""
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
        f"{settings.API_V1_STR}/projects/{project2.project_id}/baseline-logs/{baseline.baseline_id}/cost-elements-by-wbe",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert "Baseline log not found" in response.json()["detail"]
