"""Tests for Baseline Log API routes."""
import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.api.routes.baseline_logs import (
    create_baseline_cost_elements_for_baseline_log,
)
from app.core.config import settings
from app.models import (
    WBE,
    BaselineCostElement,
    BaselineLog,
    BaselineLogCreate,
    CostElement,
    CostElementCreate,
    CostElementType,
    CostElementTypeCreate,
    CostRegistration,
    Department,
    DepartmentCreate,
    EarnedValueEntry,
    EarnedValueEntryCreate,
    Forecast,
    ForecastCreate,
    Project,
    ProjectCreate,
    UserCreate,
    WBECreate,
)


def test_create_baseline_cost_elements_with_cost_elements(db: Session) -> None:
    """Test creating baseline cost elements with cost elements."""

    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Cost Elements Test Project",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create a WBE
    wbe_in = WBECreate(
        machine_type="Test Machine",
        project_id=project.project_id,
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    # Create Department and CostElementType
    unique_dept_code = f"DEPT_{uuid.uuid4().hex[:8]}"
    dept_in = DepartmentCreate(
        department_code=unique_dept_code,
        department_name="Test Department",
    )
    dept = Department.model_validate(dept_in)
    db.add(dept)
    db.commit()
    db.refresh(dept)

    unique_type_code = f"TYPE_{uuid.uuid4().hex[:8]}"
    cost_element_type_in = CostElementTypeCreate(
        type_code=unique_type_code,
        type_name="Test Type",
        category_type="labor",
        department_id=dept.department_id,
    )
    cost_element_type = CostElementType.model_validate(cost_element_type_in)
    db.add(cost_element_type)
    db.commit()
    db.refresh(cost_element_type)

    # Create a cost element
    cost_element_in = CostElementCreate(
        department_code=unique_dept_code,
        department_name="Test Department",
        budget_bac=Decimal("50000.00"),
        revenue_plan=Decimal("60000.00"),
        wbe_id=wbe.wbe_id,
        cost_element_type_id=cost_element_type.cost_element_type_id,
    )
    cost_element = CostElement.model_validate(cost_element_in)
    db.add(cost_element)
    db.commit()
    db.refresh(cost_element)

    # Create a baseline log
    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="Initial baseline",
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

    # Verify BaselineCostElement was created
    baseline_cost_elements = db.exec(
        select(BaselineCostElement).where(
            BaselineCostElement.baseline_id == baseline.baseline_id
        )
    ).all()
    assert len(baseline_cost_elements) == 1
    bce = baseline_cost_elements[0]
    assert bce.cost_element_id == cost_element.cost_element_id
    assert bce.budget_bac == Decimal("50000.00")
    assert bce.revenue_plan == Decimal("60000.00")
    assert bce.actual_ac == Decimal("0.00")  # No cost registrations yet
    assert bce.forecast_eac is None  # No forecast yet
    assert bce.earned_ev is None  # No earned value yet


def test_create_baseline_cost_elements_with_no_cost_elements(db: Session) -> None:
    """Test creating baseline cost elements with no cost elements."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Empty Project",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create a baseline log (no cost elements in project)
    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="Empty baseline",
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

    # Verify no BaselineCostElement was created (no cost elements)
    baseline_cost_elements = db.exec(
        select(BaselineCostElement).where(
            BaselineCostElement.baseline_id == baseline.baseline_id
        )
    ).all()
    assert len(baseline_cost_elements) == 0


def test_create_baseline_cost_elements_aggregates_actual_cost(db: Session) -> None:
    """Test that baseline cost elements aggregates actual cost from cost registrations."""

    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Actual Cost Test",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create a WBE
    wbe_in = WBECreate(
        machine_type="Test Machine",
        project_id=project.project_id,
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    # Create Department and CostElementType
    unique_dept_code = f"DEPT_{uuid.uuid4().hex[:8]}"
    dept_in = DepartmentCreate(
        department_code=unique_dept_code,
        department_name="Test Department",
    )
    dept = Department.model_validate(dept_in)
    db.add(dept)
    db.commit()
    db.refresh(dept)

    unique_type_code = f"TYPE_{uuid.uuid4().hex[:8]}"
    cost_element_type_in = CostElementTypeCreate(
        type_code=unique_type_code,
        type_name="Test Type",
        category_type="labor",
        department_id=dept.department_id,
    )
    cost_element_type = CostElementType.model_validate(cost_element_type_in)
    db.add(cost_element_type)
    db.commit()
    db.refresh(cost_element_type)

    # Create a cost element
    cost_element_in = CostElementCreate(
        department_code=unique_dept_code,
        department_name="Test Department",
        budget_bac=Decimal("50000.00"),
        revenue_plan=Decimal("60000.00"),
        wbe_id=wbe.wbe_id,
        cost_element_type_id=cost_element_type.cost_element_type_id,
    )
    cost_element = CostElement.model_validate(cost_element_in)
    db.add(cost_element)
    db.commit()
    db.refresh(cost_element)

    # Create cost registrations
    cr1 = CostRegistration(
        cost_element_id=cost_element.cost_element_id,
        registration_date=date(2024, 1, 10),
        amount=Decimal("10000.00"),
        cost_category="labor",
        description="First cost",
        created_by_id=user.id,
    )
    db.add(cr1)

    cr2 = CostRegistration(
        cost_element_id=cost_element.cost_element_id,
        registration_date=date(2024, 1, 12),
        amount=Decimal("5000.00"),
        cost_category="materials",
        description="Second cost",
        created_by_id=user.id,
    )
    db.add(cr2)
    db.commit()

    # Create a baseline log
    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="Baseline with costs",
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

    # Verify actual_ac was aggregated
    baseline_cost_elements = db.exec(
        select(BaselineCostElement).where(
            BaselineCostElement.baseline_id == baseline.baseline_id
        )
    ).all()
    assert len(baseline_cost_elements) == 1
    bce = baseline_cost_elements[0]
    assert bce.actual_ac == Decimal("15000.00")  # 10000 + 5000


def test_create_baseline_cost_elements_includes_forecast_eac_if_exists(
    db: Session,
) -> None:
    """Test that baseline cost elements includes forecast EAC if current forecast exists."""

    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Forecast Test",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create a WBE
    wbe_in = WBECreate(
        machine_type="Test Machine",
        project_id=project.project_id,
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    # Create Department and CostElementType
    unique_dept_code = f"DEPT_{uuid.uuid4().hex[:8]}"
    dept_in = DepartmentCreate(
        department_code=unique_dept_code,
        department_name="Test Department",
    )
    dept = Department.model_validate(dept_in)
    db.add(dept)
    db.commit()
    db.refresh(dept)

    unique_type_code = f"TYPE_{uuid.uuid4().hex[:8]}"
    cost_element_type_in = CostElementTypeCreate(
        type_code=unique_type_code,
        type_name="Test Type",
        category_type="labor",
        department_id=dept.department_id,
    )
    cost_element_type = CostElementType.model_validate(cost_element_type_in)
    db.add(cost_element_type)
    db.commit()
    db.refresh(cost_element_type)

    # Create a cost element
    cost_element_in = CostElementCreate(
        department_code=unique_dept_code,
        department_name="Test Department",
        budget_bac=Decimal("50000.00"),
        revenue_plan=Decimal("60000.00"),
        wbe_id=wbe.wbe_id,
        cost_element_type_id=cost_element_type.cost_element_type_id,
    )
    cost_element = CostElement.model_validate(cost_element_in)
    db.add(cost_element)
    db.commit()
    db.refresh(cost_element)

    # Create a current forecast
    forecast_in = ForecastCreate(
        cost_element_id=cost_element.cost_element_id,
        forecast_date=date(2024, 1, 10),
        estimate_at_completion=Decimal("52000.00"),
        forecast_type="revised",
        is_current=True,
        estimator_id=user.id,
    )
    forecast = Forecast.model_validate(forecast_in)
    db.add(forecast)
    db.commit()

    # Create a baseline log
    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="Baseline with forecast",
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

    # Verify forecast_eac was included
    baseline_cost_elements = db.exec(
        select(BaselineCostElement).where(
            BaselineCostElement.baseline_id == baseline.baseline_id
        )
    ).all()
    assert len(baseline_cost_elements) == 1
    bce = baseline_cost_elements[0]
    assert bce.forecast_eac == Decimal("52000.00")


def test_create_baseline_cost_elements_includes_earned_ev_if_exists(
    db: Session,
) -> None:
    """Test that baseline cost elements includes earned value if latest earned value entry exists."""

    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Earned Value Test",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create a WBE
    wbe_in = WBECreate(
        machine_type="Test Machine",
        project_id=project.project_id,
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    # Create Department and CostElementType
    unique_dept_code = f"DEPT_{uuid.uuid4().hex[:8]}"
    dept_in = DepartmentCreate(
        department_code=unique_dept_code,
        department_name="Test Department",
    )
    dept = Department.model_validate(dept_in)
    db.add(dept)
    db.commit()
    db.refresh(dept)

    unique_type_code = f"TYPE_{uuid.uuid4().hex[:8]}"
    cost_element_type_in = CostElementTypeCreate(
        type_code=unique_type_code,
        type_name="Test Type",
        category_type="labor",
        department_id=dept.department_id,
    )
    cost_element_type = CostElementType.model_validate(cost_element_type_in)
    db.add(cost_element_type)
    db.commit()
    db.refresh(cost_element_type)

    # Create a cost element
    cost_element_in = CostElementCreate(
        department_code=unique_dept_code,
        department_name="Test Department",
        budget_bac=Decimal("50000.00"),
        revenue_plan=Decimal("60000.00"),
        wbe_id=wbe.wbe_id,
        cost_element_type_id=cost_element_type.cost_element_type_id,
    )
    cost_element = CostElement.model_validate(cost_element_in)
    db.add(cost_element)
    db.commit()
    db.refresh(cost_element)

    # Create earned value entries (older and newer)
    ev1_in = EarnedValueEntryCreate(
        cost_element_id=cost_element.cost_element_id,
        completion_date=date(2024, 1, 5),
        percent_complete=Decimal("20.00"),
        earned_value=Decimal("10000.00"),
        created_by_id=user.id,
    )
    ev1 = EarnedValueEntry.model_validate(ev1_in)
    db.add(ev1)

    ev2_in = EarnedValueEntryCreate(
        cost_element_id=cost_element.cost_element_id,
        completion_date=date(2024, 1, 12),
        percent_complete=Decimal("30.00"),
        earned_value=Decimal("15000.00"),
        created_by_id=user.id,
    )
    ev2 = EarnedValueEntry.model_validate(ev2_in)
    db.add(ev2)
    db.commit()

    # Create a baseline log
    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="Baseline with earned value",
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

    # Verify earned_ev was included (should be latest by completion_date)
    baseline_cost_elements = db.exec(
        select(BaselineCostElement).where(
            BaselineCostElement.baseline_id == baseline.baseline_id
        )
    ).all()
    assert len(baseline_cost_elements) == 1
    bce = baseline_cost_elements[0]
    assert bce.earned_ev == Decimal("15000.00")  # Latest earned value


# Phase 6: API Endpoints Tests
def test_list_baseline_logs_for_project(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test listing baseline logs for a project."""
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
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create multiple baseline logs
    baseline1_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="First baseline",
        project_id=project.project_id,
        created_by_id=user.id,
    )
    baseline1 = BaselineLog.model_validate(baseline1_in)
    db.add(baseline1)

    baseline2_in = BaselineLogCreate(
        baseline_type="earned_value",
        baseline_date=date(2024, 2, 1),
        milestone_type="engineering_complete",
        description="Second baseline",
        project_id=project.project_id,
        created_by_id=user.id,
    )
    baseline2 = BaselineLog.model_validate(baseline2_in)
    db.add(baseline2)
    db.commit()

    # Call API
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) == 2
    baseline_ids = [item["baseline_id"] for item in content]
    assert str(baseline1.baseline_id) in baseline_ids
    assert str(baseline2.baseline_id) in baseline_ids


def test_list_baseline_logs_empty_project(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test listing baseline logs for a project with no baselines."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Empty Project",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Call API
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content == []


def test_list_baseline_logs_project_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test listing baseline logs for a non-existent project."""
    fake_project_id = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/projects/{fake_project_id}/baseline-logs/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert "Project not found" in content["detail"]


def test_list_baseline_logs_filters_cancelled(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test that list endpoint can filter out cancelled baselines."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Filter Test Project",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create active baseline
    baseline1_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="Active baseline",
        project_id=project.project_id,
        created_by_id=user.id,
    )
    baseline1 = BaselineLog.model_validate(baseline1_in)
    db.add(baseline1)

    # Create cancelled baseline
    baseline2_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 20),
        milestone_type="kickoff",
        description="Cancelled baseline",
        project_id=project.project_id,
        created_by_id=user.id,
        is_cancelled=True,
    )
    baseline2 = BaselineLog.model_validate(baseline2_in)
    db.add(baseline2)
    db.commit()

    # Call API without filter (should return all)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) == 2

    # Call API with exclude_cancelled=True (should filter out cancelled)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/?exclude_cancelled=true",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) == 1
    assert content[0]["baseline_id"] == str(baseline1.baseline_id)
    assert content[0]["is_cancelled"] is False


def test_read_baseline_log(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test reading a single baseline log."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Read Test Project",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create a baseline log
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

    # Call API
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline.baseline_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["baseline_id"] == str(baseline.baseline_id)
    assert content["baseline_type"] == "schedule"
    assert content["milestone_type"] == "kickoff"
    assert content["project_id"] == str(project.project_id)


def test_read_baseline_log_not_found(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test reading a non-existent baseline log."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Not Found Test",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    fake_baseline_id = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{fake_baseline_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert "Baseline log not found" in content["detail"]


def test_read_baseline_log_wrong_project(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test reading a baseline log that belongs to a different project."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create two projects
    project1_in = ProjectCreate(
        project_name="Project 1",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project1 = Project.model_validate(project1_in)
    db.add(project1)

    project2_in = ProjectCreate(
        project_name="Project 2",
        customer_name="Test Customer",
        contract_value=Decimal("200000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project2 = Project.model_validate(project2_in)
    db.add(project2)
    db.commit()
    db.refresh(project1)
    db.refresh(project2)

    # Create a baseline log for project1
    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="Baseline for project 1",
        project_id=project1.project_id,
        created_by_id=user.id,
    )
    baseline = BaselineLog.model_validate(baseline_in)
    db.add(baseline)
    db.commit()
    db.refresh(baseline)

    # Try to read it via project2 (should fail)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project2.project_id}/baseline-logs/{baseline.baseline_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert "Baseline log not found" in content["detail"]


# Phase 7: Create Endpoint Tests
def test_create_baseline_log(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a baseline log."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Create Test Project",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create baseline via API
    data = {
        "baseline_type": "schedule",
        "baseline_date": "2024-01-15",
        "milestone_type": "kickoff",
        "description": "Test baseline creation",
    }
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["baseline_type"] == "schedule"
    assert content["milestone_type"] == "kickoff"
    assert content["project_id"] == str(project.project_id)
    assert content["description"] == "Test baseline creation"
    assert content["is_cancelled"] is False
    assert "baseline_id" in content
    assert "created_by_id" in content


# Phase 8: Update and Cancel Endpoint Tests
def test_update_baseline_log(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating a baseline log."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Update Test Project",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create a baseline log
    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="Original description",
        project_id=project.project_id,
        created_by_id=user.id,
    )
    baseline = BaselineLog.model_validate(baseline_in)
    db.add(baseline)
    db.commit()
    db.refresh(baseline)

    # Update baseline via API
    data = {
        "description": "Updated description",
        "baseline_date": "2024-01-20",
    }
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline.baseline_id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["description"] == "Updated description"
    assert content["baseline_date"] == "2024-01-20"
    assert content["baseline_type"] == "schedule"  # Unchanged
    assert content["milestone_type"] == "kickoff"  # Unchanged


def test_update_baseline_log_not_found(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating a non-existent baseline log."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Not Found Test",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    fake_baseline_id = uuid.uuid4()
    data = {"description": "Updated"}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{fake_baseline_id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    content = response.json()
    assert "Baseline log not found" in content["detail"]


def test_update_baseline_log_wrong_project(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating a baseline log that belongs to a different project."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create two projects
    project1_in = ProjectCreate(
        project_name="Project 1",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project1 = Project.model_validate(project1_in)
    db.add(project1)

    project2_in = ProjectCreate(
        project_name="Project 2",
        customer_name="Test Customer",
        contract_value=Decimal("200000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project2 = Project.model_validate(project2_in)
    db.add(project2)
    db.commit()
    db.refresh(project1)
    db.refresh(project2)

    # Create a baseline log for project1
    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="Baseline for project 1",
        project_id=project1.project_id,
        created_by_id=user.id,
    )
    baseline = BaselineLog.model_validate(baseline_in)
    db.add(baseline)
    db.commit()
    db.refresh(baseline)

    # Try to update it via project2 (should fail)
    data = {"description": "Updated"}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project2.project_id}/baseline-logs/{baseline.baseline_id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    content = response.json()
    assert "Baseline log not found" in content["detail"]


def test_update_baseline_log_invalid_baseline_type(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating a baseline log with invalid baseline_type."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Invalid Test",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create a baseline log
    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="Original",
        project_id=project.project_id,
        created_by_id=user.id,
    )
    baseline = BaselineLog.model_validate(baseline_in)
    db.add(baseline)
    db.commit()
    db.refresh(baseline)

    # Try to update with invalid baseline_type
    data = {"baseline_type": "invalid_type"}
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline.baseline_id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 400
    content = response.json()
    assert "Invalid baseline_type" in content["detail"]


def test_cancel_baseline_log(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test cancelling a baseline log."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Cancel Test Project",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create a baseline log
    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="Baseline to cancel",
        project_id=project.project_id,
        created_by_id=user.id,
    )
    baseline = BaselineLog.model_validate(baseline_in)
    db.add(baseline)
    db.commit()
    db.refresh(baseline)

    # Cancel baseline via API
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline.baseline_id}/cancel",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["is_cancelled"] is True
    assert content["baseline_id"] == str(baseline.baseline_id)


def test_cancel_baseline_log_not_found(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test cancelling a non-existent baseline log."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Not Found Test",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    fake_baseline_id = uuid.uuid4()
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{fake_baseline_id}/cancel",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert "Baseline log not found" in content["detail"]


def test_cancel_baseline_log_already_cancelled(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test cancelling a baseline log that is already cancelled."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Already Cancelled Test",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create a cancelled baseline log
    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="Already cancelled",
        project_id=project.project_id,
        created_by_id=user.id,
        is_cancelled=True,
    )
    baseline = BaselineLog.model_validate(baseline_in)
    db.add(baseline)
    db.commit()
    db.refresh(baseline)

    # Try to cancel again (should still work, just sets is_cancelled=True again)
    response = client.put(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline.baseline_id}/cancel",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["is_cancelled"] is True


def test_create_baseline_cost_elements_creates_records(db: Session) -> None:
    """Helper creates baseline cost elements and updates baseline metadata."""

    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Refactored Test Project",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create a WBE
    wbe_in = WBECreate(
        machine_type="Test Machine",
        project_id=project.project_id,
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    # Create Department and CostElementType
    unique_dept_code = f"DEPT_{uuid.uuid4().hex[:8]}"
    dept_in = DepartmentCreate(
        department_code=unique_dept_code,
        department_name="Test Department",
    )
    dept = Department.model_validate(dept_in)
    db.add(dept)
    db.commit()
    db.refresh(dept)

    unique_type_code = f"TYPE_{uuid.uuid4().hex[:8]}"
    cost_element_type_in = CostElementTypeCreate(
        type_code=unique_type_code,
        type_name="Test Type",
        category_type="labor",
        department_id=dept.department_id,
    )
    cost_element_type = CostElementType.model_validate(cost_element_type_in)
    db.add(cost_element_type)
    db.commit()
    db.refresh(cost_element_type)

    # Create a cost element
    cost_element_in = CostElementCreate(
        department_code=unique_dept_code,
        department_name="Test Department",
        budget_bac=Decimal("50000.00"),
        revenue_plan=Decimal("60000.00"),
        wbe_id=wbe.wbe_id,
        cost_element_type_id=cost_element_type.cost_element_type_id,
    )
    cost_element = CostElement.model_validate(cost_element_in)
    db.add(cost_element)
    db.commit()
    db.refresh(cost_element)

    # Create a baseline log with department and is_pmb
    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="Initial baseline",
        department="Engineering",
        is_pmb=True,
        project_id=project.project_id,
        created_by_id=user.id,
    )
    baseline = BaselineLog.model_validate(baseline_in)
    db.add(baseline)
    db.commit()
    db.refresh(baseline)

    # Call refactored function
    create_baseline_cost_elements_for_baseline_log(
        session=db,
        baseline_log=baseline,
        created_by_id=user.id,
        department="Engineering",
        is_pmb=True,
    )
    db.commit()
    db.refresh(baseline)

    # Verify BaselineCostElement WAS created
    baseline_cost_elements = db.exec(
        select(BaselineCostElement).where(
            BaselineCostElement.baseline_id == baseline.baseline_id
        )
    ).all()
    assert len(baseline_cost_elements) == 1
    bce = baseline_cost_elements[0]
    assert bce.cost_element_id == cost_element.cost_element_id
    assert bce.budget_bac == Decimal("50000.00")
    assert bce.revenue_plan == Decimal("60000.00")

    # Verify department and is_pmb are set on BaselineLog
    assert baseline.department == "Engineering"
    assert baseline.is_pmb is True


def test_create_baseline_log_with_department_and_is_pmb_via_api(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test POST endpoint accepts department and is_pmb fields."""

    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="API Test Project",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create baseline via API with department and is_pmb
    data = {
        "baseline_type": "combined",
        "baseline_date": "2024-01-15",
        "milestone_type": "kickoff",
        "description": "PMB baseline",
        "department": "Engineering",
        "is_pmb": True,
    }
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["department"] == "Engineering"
    assert content["is_pmb"] is True
    uuid.UUID(content["baseline_id"])  # Validate parseable UUID


def test_get_baseline_summary_uses_baseline_log_data(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test GET snapshot endpoint returns data derived directly from BaselineLog."""

    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Summary Test Project",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create a WBE and cost element
    wbe_in = WBECreate(
        machine_type="Test Machine",
        project_id=project.project_id,
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    unique_dept_code = f"DEPT_{uuid.uuid4().hex[:8]}"
    dept_in = DepartmentCreate(
        department_code=unique_dept_code,
        department_name="Test Department",
    )
    dept = Department.model_validate(dept_in)
    db.add(dept)
    db.commit()
    db.refresh(dept)

    unique_type_code = f"TYPE_{uuid.uuid4().hex[:8]}"
    cost_element_type_in = CostElementTypeCreate(
        type_code=unique_type_code,
        type_name="Test Type",
        category_type="labor",
        department_id=dept.department_id,
    )
    cost_element_type = CostElementType.model_validate(cost_element_type_in)
    db.add(cost_element_type)
    db.commit()
    db.refresh(cost_element_type)

    cost_element_in = CostElementCreate(
        department_code=unique_dept_code,
        department_name="Test Department",
        budget_bac=Decimal("50000.00"),
        revenue_plan=Decimal("60000.00"),
        wbe_id=wbe.wbe_id,
        cost_element_type_id=cost_element_type.cost_element_type_id,
    )
    cost_element = CostElement.model_validate(cost_element_in)
    db.add(cost_element)
    db.commit()
    db.refresh(cost_element)

    # Create baseline log with department and is_pmb (NO BaselineSnapshot)
    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="Test baseline",
        department="Engineering",
        is_pmb=True,
        project_id=project.project_id,
        created_by_id=user.id,
    )
    baseline = BaselineLog.model_validate(baseline_in)
    db.add(baseline)
    db.commit()
    db.refresh(baseline)

    # Create BaselineCostElement directly (no BaselineSnapshot)
    from app.models import BaselineCostElementCreate

    bce_in = BaselineCostElementCreate(
        baseline_id=baseline.baseline_id,
        cost_element_id=cost_element.cost_element_id,
        budget_bac=Decimal("50000.00"),
        revenue_plan=Decimal("60000.00"),
    )
    bce = BaselineCostElement.model_validate(bce_in)
    db.add(bce)
    db.commit()

    # Call GET snapshot endpoint - should work without BaselineSnapshot
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline.baseline_id}/snapshot",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()

    # Verify response uses BaselineLog data (not BaselineSnapshot)
    assert content["baseline_id"] == str(baseline.baseline_id)
    assert content["baseline_date"] == "2024-01-15"
    assert content["milestone_type"] == "kickoff"
    assert content["description"] == "Test baseline"
    assert content["total_budget_bac"] == "50000.00"
    assert content["total_revenue_plan"] == "60000.00"
    assert content["cost_element_count"] == 1
