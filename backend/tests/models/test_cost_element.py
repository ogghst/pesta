"""Tests for CostElement model."""
import uuid
from datetime import date

from sqlmodel import Session

from app import crud
from app.models import (
    WBE,
    CostElement,
    CostElementCreate,
    CostElementPublic,
    CostElementType,
    CostElementTypeCreate,
    Project,
    ProjectCreate,
    UserCreate,
    WBECreate,
)


def test_cost_element_has_version_status_branch_fields(db: Session) -> None:
    """Test that CostElement model has version, status (versioning), and branch fields from BranchVersionMixin."""
    # Create hierarchy: User -> Project -> WBE -> CostElementType -> CostElement
    email = f"pm_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    pm_user = crud.create_user(session=db, user_create=user_in)

    project_in = ProjectCreate(
        project_name="Cost Element Test Project",
        customer_name="Test Customer",
        contract_value=100000.00,
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=pm_user.id,
        business_status="active",
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Test Machine",
        revenue_allocation=50000.00,
        business_status="designing",
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    # Create cost element type
    cet_in = CostElementTypeCreate(
        type_code=f"test_eng_{uuid.uuid4().hex[:6]}",
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
        department_name="Engineering Department",
        budget_bac=10000.00,
        revenue_plan=12000.00,
        business_status="active",
        notes="Primary cost element",
    )

    ce = CostElement.model_validate(ce_in)

    # Check that version, status (versioning), and branch fields exist with defaults
    assert hasattr(ce, "version")
    assert ce.version == 1
    assert hasattr(
        ce, "status"
    )  # Note: CostElement has both business status and versioning status
    assert hasattr(ce, "branch")
    assert ce.branch == "main"


def test_create_cost_element(db: Session) -> None:
    """Test creating a cost element."""
    # Create hierarchy: User -> Project -> WBE -> CostElementType -> CostElement
    email = f"pm_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    pm_user = crud.create_user(session=db, user_create=user_in)

    project_in = ProjectCreate(
        project_name="Cost Element Test Project",
        customer_name="Test Customer",
        contract_value=100000.00,
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=pm_user.id,
        business_status="active",
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Test Machine",
        revenue_allocation=50000.00,
        business_status="designing",
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    # Create cost element type
    cet_in = CostElementTypeCreate(
        type_code=f"test_eng_{uuid.uuid4().hex[:6]}",
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
        department_name="Engineering Department",
        budget_bac=10000.00,
        revenue_plan=12000.00,
        business_status="active",
        notes="Primary cost element",
    )

    ce = CostElement.model_validate(ce_in)
    db.add(ce)
    db.commit()
    db.refresh(ce)

    # Verify cost element was created
    assert ce.cost_element_id is not None
    assert ce.department_code == "ENG"
    assert ce.department_name == "Engineering Department"
    assert ce.budget_bac == 10000.00
    assert ce.revenue_plan == 12000.00
    assert ce.business_status == "active"
    assert ce.wbe_id == wbe.wbe_id
    assert ce.cost_element_type_id == cet.cost_element_type_id
    assert hasattr(ce, "wbe")  # Relationship should exist
    assert hasattr(ce, "cost_element_type")  # Relationship should exist


def test_cost_element_hierarchy(db: Session) -> None:
    """Test the full hierarchy: Project -> WBE -> CostElement."""
    # Create hierarchy
    email = f"pm_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    pm_user = crud.create_user(session=db, user_create=user_in)

    project_in = ProjectCreate(
        project_name="Hierarchy Test",
        customer_name="Customer",
        contract_value=100000.00,
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=pm_user.id,
        business_status="active",
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Machine",
        revenue_allocation=50000.00,
        business_status="designing",
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    cet_in = CostElementTypeCreate(
        type_code=f"test_dept_{uuid.uuid4().hex[:6]}",
        type_name="Test Department",
        category_type="other",
        display_order=1,
        is_active=True,
    )
    cet = CostElementType.model_validate(cet_in)
    db.add(cet)
    db.commit()
    db.refresh(cet)

    ce_in = CostElementCreate(
        wbe_id=wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="TEST",
        department_name="Test Department",
        budget_bac=5000.00,
        revenue_plan=6000.00,
        business_status="active",
    )
    ce = CostElement.model_validate(ce_in)
    db.add(ce)
    db.commit()
    db.refresh(ce)

    # Verify hierarchy
    assert ce.wbe_id == wbe.wbe_id
    assert wbe.project_id == project.project_id
    assert ce.cost_element_type_id == cet.cost_element_type_id


def test_cost_element_validation(db: Session) -> None:
    """Test cost element validation rules."""
    # Create hierarchy
    email = f"pm_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    pm_user = crud.create_user(session=db, user_create=user_in)

    project_in = ProjectCreate(
        project_name="Validation Test",
        customer_name="Customer",
        contract_value=100000.00,
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=pm_user.id,
        business_status="active",
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Machine",
        revenue_allocation=50000.00,
        business_status="designing",
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    cet_in = CostElementTypeCreate(
        type_code=f"test_val_{uuid.uuid4().hex[:6]}",
        type_name="Test Validation",
        category_type="other",
        display_order=1,
        is_active=True,
    )
    cet = CostElementType.model_validate(cet_in)
    db.add(cet)
    db.commit()
    db.refresh(cet)

    # Test budget_bac >= 0
    ce_in = CostElementCreate(
        wbe_id=wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="TEST",
        department_name="Test Dept",
        budget_bac=0.00,  # Zero budget should be allowed
        revenue_plan=0.00,
        business_status="planned",
    )
    ce = CostElement.model_validate(ce_in)
    db.add(ce)
    db.commit()
    db.refresh(ce)
    assert ce.budget_bac == 0.00


def test_cost_element_type_relationship(db: Session) -> None:
    """Test that cost element references cost element type correctly."""
    # Create hierarchy
    email = f"pm_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    pm_user = crud.create_user(session=db, user_create=user_in)

    project_in = ProjectCreate(
        project_name="Type Relationship Test",
        customer_name="Customer",
        contract_value=100000.00,
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=pm_user.id,
        business_status="active",
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Machine",
        revenue_allocation=50000.00,
        business_status="designing",
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    cet_in = CostElementTypeCreate(
        type_code=f"test_rel_{uuid.uuid4().hex[:6]}",
        type_name="Test Relationship",
        category_type="engineering_electrical",
        tracks_hours=True,
        display_order=1,
        is_active=True,
    )
    cet = CostElementType.model_validate(cet_in)
    db.add(cet)
    db.commit()
    db.refresh(cet)

    ce_in = CostElementCreate(
        wbe_id=wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="ELEC",
        department_name="Electrical",
        budget_bac=15000.00,
        revenue_plan=18000.00,
        business_status="active",
    )
    ce = CostElement.model_validate(ce_in)
    db.add(ce)
    db.commit()
    db.refresh(ce)

    # Verify type relationship
    assert ce.cost_element_type_id == cet.cost_element_type_id


def test_cost_element_public_schema() -> None:
    """Test CostElementPublic schema for API responses."""
    ce_id = uuid.uuid4()
    wbe_id = uuid.uuid4()
    cet_id = uuid.uuid4()

    ce_public = CostElementPublic(
        cost_element_id=ce_id,
        wbe_id=wbe_id,
        cost_element_type_id=cet_id,
        department_code="SALES",
        department_name="Sales Department",
        budget_bac=5000.00,
        revenue_plan=6000.00,
        business_status="active",
    )

    assert ce_public.cost_element_id == ce_id
    assert ce_public.department_code == "SALES"
    assert ce_public.budget_bac == 5000.00
