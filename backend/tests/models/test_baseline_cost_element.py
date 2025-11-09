"""Tests for BaselineCostElement model."""
import uuid
from datetime import date
from decimal import Decimal

from sqlmodel import Session

from app import crud
from app.models import (
    BaselineCostElement,
    BaselineCostElementCreate,
    BaselineCostElementPublic,
    CostElement,
    CostElementCreate,
    Project,
    ProjectCreate,
    UserCreate,
)


def test_create_baseline_cost_element(db: Session) -> None:
    """Test creating a baseline cost element entry."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Test Project",
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

    # Create a WBE (needed for CostElement)
    from app.models import WBE, WBECreate

    wbe_in = WBECreate(
        machine_type="Test Machine",
        project_id=project.project_id,
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    # Create a CostElementType (needed for CostElement)
    from app.models import (
        CostElementType,
        CostElementTypeCreate,
        Department,
        DepartmentCreate,
    )

    unique_code = f"DEPT_{uuid.uuid4().hex[:8]}"
    dept_in = DepartmentCreate(
        department_code=unique_code,
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
        department_code=unique_code,
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

    # Create a baseline log (needed for BaselineCostElement)
    from app.models import BaselineLog, BaselineLogCreate

    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        description="Initial schedule baseline",
        project_id=project.project_id,
        created_by_id=user.id,
    )
    baseline = BaselineLog.model_validate(baseline_in)
    db.add(baseline)
    db.commit()
    db.refresh(baseline)

    # Create a baseline cost element
    baseline_cost_element_in = BaselineCostElementCreate(
        baseline_id=baseline.baseline_id,
        cost_element_id=cost_element.cost_element_id,
        budget_bac=Decimal("50000.00"),
        revenue_plan=Decimal("60000.00"),
        actual_ac=Decimal("10000.00"),
        forecast_eac=Decimal("52000.00"),
        earned_ev=Decimal("25000.00"),
        percent_complete=Decimal("55.00"),
    )

    baseline_cost_element = BaselineCostElement.model_validate(baseline_cost_element_in)
    db.add(baseline_cost_element)
    db.commit()
    db.refresh(baseline_cost_element)

    # Verify baseline cost element was created
    assert baseline_cost_element.baseline_cost_element_id is not None
    assert baseline_cost_element.baseline_id == baseline.baseline_id
    assert baseline_cost_element.cost_element_id == cost_element.cost_element_id
    assert baseline_cost_element.budget_bac == Decimal("50000.00")
    assert baseline_cost_element.revenue_plan == Decimal("60000.00")
    assert baseline_cost_element.actual_ac == Decimal("10000.00")
    assert baseline_cost_element.forecast_eac == Decimal("52000.00")
    assert baseline_cost_element.earned_ev == Decimal("25000.00")
    assert baseline_cost_element.percent_complete == Decimal("55.00")
    assert hasattr(baseline_cost_element, "baseline_log")  # Relationship should exist
    assert hasattr(baseline_cost_element, "cost_element")  # Relationship should exist


def test_baseline_cost_element_relationships(db: Session) -> None:
    """Test that baseline cost element references baseline log and cost element correctly."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Test Project",
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
    from app.models import WBE, WBECreate

    wbe_in = WBECreate(
        machine_type="Test Machine",
        project_id=project.project_id,
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    # Create a Department and CostElementType
    from app.models import (
        CostElementType,
        CostElementTypeCreate,
        Department,
        DepartmentCreate,
    )

    unique_code = f"DEPT_{uuid.uuid4().hex[:8]}"
    dept_in = DepartmentCreate(
        department_code=unique_code,
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
        department_code=unique_code,
        department_name="Test Department",
        budget_bac=Decimal("30000.00"),
        revenue_plan=Decimal("35000.00"),
        wbe_id=wbe.wbe_id,
        cost_element_type_id=cost_element_type.cost_element_type_id,
    )
    cost_element = CostElement.model_validate(cost_element_in)
    db.add(cost_element)
    db.commit()
    db.refresh(cost_element)

    # Create a baseline log
    from app.models import BaselineLog, BaselineLogCreate

    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 2, 1),
        milestone_type="kickoff",
        description="Test baseline",
        project_id=project.project_id,
        created_by_id=user.id,
    )
    baseline = BaselineLog.model_validate(baseline_in)
    db.add(baseline)
    db.commit()
    db.refresh(baseline)

    # Create a baseline cost element
    baseline_cost_element_in = BaselineCostElementCreate(
        baseline_id=baseline.baseline_id,
        cost_element_id=cost_element.cost_element_id,
        budget_bac=Decimal("30000.00"),
        revenue_plan=Decimal("35000.00"),
        percent_complete=Decimal("25.00"),
    )
    baseline_cost_element = BaselineCostElement.model_validate(baseline_cost_element_in)
    db.add(baseline_cost_element)
    db.commit()
    db.refresh(baseline_cost_element)

    assert baseline_cost_element.baseline_id == baseline.baseline_id
    assert baseline_cost_element.cost_element_id == cost_element.cost_element_id


def test_baseline_cost_element_decimal_fields(db: Session) -> None:
    """Test that decimal fields are handled correctly."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Test Project",
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
    from app.models import WBE, WBECreate

    wbe_in = WBECreate(
        machine_type="Test Machine",
        project_id=project.project_id,
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    # Create a Department and CostElementType
    from app.models import (
        CostElementType,
        CostElementTypeCreate,
        Department,
        DepartmentCreate,
    )

    unique_code = f"DEPT_{uuid.uuid4().hex[:8]}"
    dept_in = DepartmentCreate(
        department_code=unique_code,
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
        department_code=unique_code,
        department_name="Test Department",
        budget_bac=Decimal("12345.67"),
        revenue_plan=Decimal("23456.78"),
        wbe_id=wbe.wbe_id,
        cost_element_type_id=cost_element_type.cost_element_type_id,
    )
    cost_element = CostElement.model_validate(cost_element_in)
    db.add(cost_element)
    db.commit()
    db.refresh(cost_element)

    # Create a baseline log
    from app.models import BaselineLog, BaselineLogCreate

    baseline_in = BaselineLogCreate(
        baseline_type="schedule",
        baseline_date=date(2024, 1, 15),
        milestone_type="kickoff",
        project_id=project.project_id,
        created_by_id=user.id,
    )
    baseline = BaselineLog.model_validate(baseline_in)
    db.add(baseline)
    db.commit()
    db.refresh(baseline)

    # Create a baseline cost element with precise decimals
    baseline_cost_element_in = BaselineCostElementCreate(
        baseline_id=baseline.baseline_id,
        cost_element_id=cost_element.cost_element_id,
        budget_bac=Decimal("12345.67"),
        revenue_plan=Decimal("23456.78"),
        actual_ac=Decimal("9999.99"),
        forecast_eac=Decimal("11111.11"),
        earned_ev=Decimal("22222.22"),
        percent_complete=Decimal("88.88"),
    )
    baseline_cost_element = BaselineCostElement.model_validate(baseline_cost_element_in)
    db.add(baseline_cost_element)
    db.commit()
    db.refresh(baseline_cost_element)

    # Verify decimal precision is maintained
    assert baseline_cost_element.budget_bac == Decimal("12345.67")
    assert baseline_cost_element.revenue_plan == Decimal("23456.78")
    assert baseline_cost_element.actual_ac == Decimal("9999.99")
    assert baseline_cost_element.forecast_eac == Decimal("11111.11")
    assert baseline_cost_element.earned_ev == Decimal("22222.22")
    assert baseline_cost_element.percent_complete == Decimal("88.88")


def test_baseline_cost_element_public_schema() -> None:
    """Test BaselineCostElementPublic schema for API responses."""
    import datetime

    baseline_cost_element_id = uuid.uuid4()
    baseline_id = uuid.uuid4()
    cost_element_id = uuid.uuid4()
    now = datetime.datetime.now(datetime.timezone.utc)

    baseline_cost_element_public = BaselineCostElementPublic(
        baseline_cost_element_id=baseline_cost_element_id,
        baseline_id=baseline_id,
        cost_element_id=cost_element_id,
        budget_bac=Decimal("10000.00"),
        revenue_plan=Decimal("12000.00"),
        actual_ac=Decimal("5000.00"),
        forecast_eac=Decimal("11000.00"),
        earned_ev=Decimal("6000.00"),
        percent_complete=Decimal("42.50"),
        created_at=now,
    )

    assert (
        baseline_cost_element_public.baseline_cost_element_id
        == baseline_cost_element_id
    )
    assert baseline_cost_element_public.baseline_id == baseline_id
    assert baseline_cost_element_public.cost_element_id == cost_element_id
    assert baseline_cost_element_public.budget_bac == Decimal("10000.00")
    assert baseline_cost_element_public.revenue_plan == Decimal("12000.00")
    assert baseline_cost_element_public.actual_ac == Decimal("5000.00")
    assert baseline_cost_element_public.forecast_eac == Decimal("11000.00")
    assert baseline_cost_element_public.earned_ev == Decimal("6000.00")
    assert baseline_cost_element_public.percent_complete == Decimal("42.50")
    assert baseline_cost_element_public.created_at == now
