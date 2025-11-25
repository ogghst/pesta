"""Tests for branch service."""

import uuid
from datetime import date

from sqlmodel import Session, select

from app.models import ChangeOrder, Project, User, UserCreate
from app.services.branch_service import BranchService


def _create_pm_user(session: Session) -> User:
    """Helper to create a project manager user."""
    email = f"pm_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    from app import crud

    return crud.create_user(session=session, user_create=user_in)


def _create_project(session: Session, pm_user: User) -> Project:
    """Helper to create a project."""
    from app.models import ProjectCreate

    project_in = ProjectCreate(
        project_name="Test Project",
        customer_name="Test Customer",
        contract_value=100000.00,
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=pm_user.id,
        business_status="active",
    )
    project = Project.model_validate(project_in)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def _create_change_order(
    session: Session, project: Project, created_by: User
) -> ChangeOrder:
    """Helper to create a change order."""
    from app.models import ChangeOrderCreate

    co_in = ChangeOrderCreate(
        project_id=project.project_id,
        created_by_id=created_by.id,
        change_order_number=f"CO-{uuid.uuid4().hex[:6].upper()}",
        title="Test Change Order",
        description="Test description",
        requesting_party="Customer",
        effective_date=date(2024, 6, 1),
        workflow_status="design",
    )
    co = ChangeOrder.model_validate(co_in)
    session.add(co)
    session.commit()
    session.refresh(co)
    return co


def test_create_branch_generates_name(db: Session) -> None:
    """Test that create_branch generates a branch name in the correct format."""
    # Create a project and change order first
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)

    # Create branch
    branch_name = BranchService.create_branch(
        session=db, change_order_id=change_order.change_order_id
    )

    # Verify branch name format: 'co-{short_id}'
    assert branch_name.startswith("co-")
    assert len(branch_name) > 3  # Should have some identifier after 'co-'


def test_create_branch_returns_unique_name(db: Session) -> None:
    """Test that create_branch returns unique branch names."""
    # Create multiple change orders and branches
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    co1 = _create_change_order(db, project, pm_user)
    co2 = _create_change_order(db, project, pm_user)

    # Create branches
    branch1 = BranchService.create_branch(
        session=db, change_order_id=co1.change_order_id
    )
    branch2 = BranchService.create_branch(
        session=db, change_order_id=co2.change_order_id
    )

    # Verify branches are unique
    assert branch1 != branch2


def test_create_branch_naming_convention(db: Session) -> None:
    """Test that branch name follows naming convention 'co-{short_id}'."""
    # Create a change order
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)

    # Create branch
    branch_name = BranchService.create_branch(
        session=db, change_order_id=change_order.change_order_id
    )

    # Verify format: starts with 'co-' and has identifier
    assert branch_name.startswith("co-")
    parts = branch_name.split("-")
    assert len(parts) >= 2
    assert parts[0] == "co"


def test_merge_branch_creates_main_entities(db: Session) -> None:
    """Test that merge_branch copies WBEs and Cost Elements into main branch."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = BranchService.create_branch(
        db, change_order_id=change_order.change_order_id
    )

    from app.models import WBE, CostElement, CostElementType, CostElementTypeCreate

    branch_wbe = WBE(
        entity_id=uuid.uuid4(),
        project_id=project.project_id,
        machine_type="Branch WBE",
        revenue_allocation=50000.00,
        business_status="designing",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_wbe)
    db.flush()
    branch_wbe_id = branch_wbe.wbe_id

    # Cost element type
    cet_in = CostElementTypeCreate(
        type_code=f"merge_{uuid.uuid4().hex[:6]}",
        type_name="Merge Type",
        category_type="engineering_mechanical",
        display_order=1,
        is_active=True,
    )
    cet = CostElementType.model_validate(cet_in)
    db.add(cet)
    db.commit()
    db.refresh(branch_wbe)
    db.refresh(cet)

    branch_cost_element = CostElement(
        entity_id=uuid.uuid4(),
        wbe_id=branch_wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="ENG",
        department_name="Engineering Branch",
        budget_bac=25000.00,
        revenue_plan=28000.00,
        business_status="planned",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_cost_element)
    db.commit()

    BranchService.merge_branch(
        session=db,
        branch=branch,
        change_order_id=change_order.change_order_id,
    )
    db.commit()

    main_wbe = db.exec(
        select(WBE)
        .where(WBE.entity_id == branch_wbe.entity_id)
        .where(WBE.branch == "main")
        .order_by(WBE.version.desc())
    ).first()
    assert main_wbe is not None
    assert main_wbe.machine_type == "Branch WBE"
    assert main_wbe.status == "active"

    main_cost_element = db.exec(
        select(CostElement)
        .where(CostElement.entity_id == branch_cost_element.entity_id)
        .where(CostElement.branch == "main")
        .order_by(CostElement.version.desc())
    ).first()
    assert main_cost_element is not None
    assert main_cost_element.department_name == "Engineering Branch"
    assert main_cost_element.status == "active"

    branch_wbe_after = db.exec(
        select(WBE).where(WBE.wbe_id == branch_wbe_id).where(WBE.branch == branch)
    ).first()
    assert branch_wbe_after is not None
    assert branch_wbe_after.status == "merged"

    branch_ce_after = db.exec(
        select(CostElement)
        .where(CostElement.cost_element_id == branch_cost_element.cost_element_id)
        .where(CostElement.branch == branch)
    ).first()
    assert branch_ce_after is not None
    assert branch_ce_after.status == "merged"
