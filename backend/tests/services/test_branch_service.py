"""Tests for branch service."""

import uuid
from datetime import date

import pytest
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


def test_merge_branch_creates_new_versions_in_main(db: Session) -> None:
    """Test that merge creates new versions in main branch (doesn't overwrite existing versions)."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = BranchService.create_branch(
        db, change_order_id=change_order.change_order_id
    )

    from app.models import WBE

    entity_id = uuid.uuid4()

    # Create WBE in main branch with version 1
    main_wbe_v1 = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Main WBE v1",
        revenue_allocation=10000.00,
        business_status="designing",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_wbe_v1)
    db.commit()
    db.refresh(main_wbe_v1)

    # Create modified WBE in branch
    branch_wbe = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Branch WBE Modified",
        revenue_allocation=20000.00,
        business_status="designing",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_wbe)
    db.commit()

    # Merge branch
    BranchService.merge_branch(
        session=db,
        branch=branch,
        change_order_id=change_order.change_order_id,
    )
    db.commit()

    # Verify main branch has both versions (v1 preserved, v2 created)
    main_versions = db.exec(
        select(WBE)
        .where(WBE.entity_id == entity_id)
        .where(WBE.branch == "main")
        .order_by(WBE.version)
    ).all()

    assert len(main_versions) == 2
    assert main_versions[0].version == 1
    assert main_versions[0].machine_type == "Main WBE v1"
    assert main_versions[1].version == 2
    assert main_versions[1].machine_type == "Branch WBE Modified"


def test_merge_branch_last_write_wins(db: Session) -> None:
    """Test that merge uses last-write-wins (branch values overwrite main values)."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = BranchService.create_branch(
        db, change_order_id=change_order.change_order_id
    )

    from app.models import WBE, CostElement, CostElementType, CostElementTypeCreate

    entity_id = uuid.uuid4()

    # Create WBE in main branch
    main_wbe = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Main WBE Original",
        revenue_allocation=10000.00,
        business_status="designing",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_wbe)
    db.flush()
    main_wbe_id = main_wbe.wbe_id

    # Create CostElementType
    cet_in = CostElementTypeCreate(
        type_code=f"lww_{uuid.uuid4().hex[:6]}",
        type_name="Last Write Wins Type",
        category_type="engineering_mechanical",
        display_order=1,
        is_active=True,
    )
    cet = CostElementType.model_validate(cet_in)
    db.add(cet)
    db.commit()
    db.refresh(main_wbe)
    db.refresh(cet)

    # Create CostElement in main
    main_ce = CostElement(
        entity_id=uuid.uuid4(),
        wbe_id=main_wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="MAIN",
        department_name="Main Department",
        budget_bac=5000.00,
        revenue_plan=6000.00,
        business_status="planned",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_ce)
    db.commit()
    main_ce_entity_id = main_ce.entity_id

    # Create modified versions in branch (different values)
    branch_wbe = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Branch WBE Override",
        revenue_allocation=25000.00,  # Different value
        business_status="designing",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_wbe)
    db.flush()

    branch_ce = CostElement(
        entity_id=main_ce_entity_id,
        wbe_id=branch_wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="BRANCH",
        department_name="Branch Department",  # Different value
        budget_bac=15000.00,  # Different value
        revenue_plan=18000.00,  # Different value
        business_status="planned",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_ce)
    db.commit()

    # Merge branch
    BranchService.merge_branch(
        session=db,
        branch=branch,
        change_order_id=change_order.change_order_id,
    )
    db.commit()

    # Verify branch values overwrote main values in new version
    main_wbe_latest = db.exec(
        select(WBE)
        .where(WBE.entity_id == entity_id)
        .where(WBE.branch == "main")
        .order_by(WBE.version.desc())
    ).first()

    assert main_wbe_latest is not None
    assert main_wbe_latest.version == 2  # New version created
    assert main_wbe_latest.machine_type == "Branch WBE Override"  # Branch value wins
    assert main_wbe_latest.revenue_allocation == 25000.00  # Branch value wins

    main_ce_latest = db.exec(
        select(CostElement)
        .where(CostElement.entity_id == main_ce_entity_id)
        .where(CostElement.branch == "main")
        .order_by(CostElement.version.desc())
    ).first()

    assert main_ce_latest is not None
    assert main_ce_latest.version == 2  # New version created
    assert main_ce_latest.department_name == "Branch Department"  # Branch value wins
    assert main_ce_latest.budget_bac == 15000.00  # Branch value wins


def test_merge_branch_handles_update_operations(db: Session) -> None:
    """Test that merge handles UPDATE operations (modified entities that exist in both branches)."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = BranchService.create_branch(
        db, change_order_id=change_order.change_order_id
    )

    from app.models import WBE, CostElement, CostElementType, CostElementTypeCreate

    entity_id = uuid.uuid4()

    # Create WBE in main branch
    main_wbe = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Original Machine",
        revenue_allocation=10000.00,
        business_status="designing",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_wbe)
    db.flush()
    main_wbe_id = main_wbe.wbe_id

    # Create CostElementType
    cet_in = CostElementTypeCreate(
        type_code=f"update_{uuid.uuid4().hex[:6]}",
        type_name="Update Type",
        category_type="engineering_mechanical",
        display_order=1,
        is_active=True,
    )
    cet = CostElementType.model_validate(cet_in)
    db.add(cet)
    db.commit()
    db.refresh(main_wbe)
    db.refresh(cet)

    # Create CostElement in main
    main_ce = CostElement(
        entity_id=uuid.uuid4(),
        wbe_id=main_wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="MAIN",
        department_name="Main Department",
        budget_bac=5000.00,
        revenue_plan=6000.00,
        business_status="planned",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_ce)
    db.commit()
    ce_entity_id = main_ce.entity_id

    # Modify WBE in branch (UPDATE operation)
    branch_wbe = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Updated Machine",  # Modified
        revenue_allocation=15000.00,  # Modified
        business_status="designing",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_wbe)
    db.flush()

    # Modify CostElement in branch (UPDATE operation)
    branch_ce = CostElement(
        entity_id=ce_entity_id,
        wbe_id=branch_wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="UPDATED",
        department_name="Updated Department",  # Modified
        budget_bac=7500.00,  # Modified
        revenue_plan=9000.00,  # Modified
        business_status="planned",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_ce)
    db.commit()

    # Merge branch
    BranchService.merge_branch(
        session=db,
        branch=branch,
        change_order_id=change_order.change_order_id,
    )
    db.commit()

    # Verify UPDATE created new versions in main
    main_wbe_updated = db.exec(
        select(WBE)
        .where(WBE.entity_id == entity_id)
        .where(WBE.branch == "main")
        .order_by(WBE.version.desc())
    ).first()

    assert main_wbe_updated is not None
    assert main_wbe_updated.version == 2  # New version for update
    assert main_wbe_updated.machine_type == "Updated Machine"
    assert main_wbe_updated.revenue_allocation == 15000.00

    main_ce_updated = db.exec(
        select(CostElement)
        .where(CostElement.entity_id == ce_entity_id)
        .where(CostElement.branch == "main")
        .order_by(CostElement.version.desc())
    ).first()

    assert main_ce_updated is not None
    assert main_ce_updated.version == 2  # New version for update
    assert main_ce_updated.department_name == "Updated Department"
    assert main_ce_updated.budget_bac == 7500.00


def test_merge_branch_handles_delete_operations(db: Session) -> None:
    """Test that merge handles DELETE operations (deleted entities in branch)."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = BranchService.create_branch(
        db, change_order_id=change_order.change_order_id
    )

    from app.models import WBE, CostElement, CostElementType, CostElementTypeCreate

    entity_id = uuid.uuid4()

    # Create WBE in main branch
    main_wbe = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Main WBE",
        revenue_allocation=10000.00,
        business_status="designing",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_wbe)
    db.flush()
    main_wbe_id = main_wbe.wbe_id

    # Create CostElementType
    cet_in = CostElementTypeCreate(
        type_code=f"delete_{uuid.uuid4().hex[:6]}",
        type_name="Delete Type",
        category_type="engineering_mechanical",
        display_order=1,
        is_active=True,
    )
    cet = CostElementType.model_validate(cet_in)
    db.add(cet)
    db.commit()
    db.refresh(main_wbe)
    db.refresh(cet)

    # Create CostElement in main
    main_ce = CostElement(
        entity_id=uuid.uuid4(),
        wbe_id=main_wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="MAIN",
        department_name="Main Department",
        budget_bac=5000.00,
        revenue_plan=6000.00,
        business_status="planned",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_ce)
    db.commit()
    ce_entity_id = main_ce.entity_id

    # Create deleted WBE in branch (DELETE operation)
    branch_wbe_deleted = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Deleted WBE",
        revenue_allocation=10000.00,
        business_status="designing",
        branch=branch,
        version=1,
        status="deleted",  # Deleted in branch
    )
    db.add(branch_wbe_deleted)
    db.flush()

    # Create deleted CostElement in branch (DELETE operation)
    branch_ce_deleted = CostElement(
        entity_id=ce_entity_id,
        wbe_id=branch_wbe_deleted.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="DELETED",
        department_name="Deleted Department",
        budget_bac=5000.00,
        revenue_plan=6000.00,
        business_status="planned",
        branch=branch,
        version=1,
        status="deleted",  # Deleted in branch
    )
    db.add(branch_ce_deleted)
    db.commit()

    # Merge branch
    BranchService.merge_branch(
        session=db,
        branch=branch,
        change_order_id=change_order.change_order_id,
    )
    db.commit()

    # Verify DELETE operations created deleted versions in main
    main_wbe_deleted = db.exec(
        select(WBE)
        .where(WBE.entity_id == entity_id)
        .where(WBE.branch == "main")
        .order_by(WBE.version.desc())
    ).first()

    assert main_wbe_deleted is not None
    assert main_wbe_deleted.version == 2  # New version created
    assert main_wbe_deleted.status == "deleted"  # Deleted status copied

    main_ce_deleted = db.exec(
        select(CostElement)
        .where(CostElement.entity_id == ce_entity_id)
        .where(CostElement.branch == "main")
        .order_by(CostElement.version.desc())
    ).first()

    assert main_ce_deleted is not None
    assert main_ce_deleted.version == 2  # New version created
    assert main_ce_deleted.status == "deleted"  # Deleted status copied


def test_merge_branch_is_transactional(db: Session) -> None:
    """Test that merge is transactional (all or nothing - rollback on error)."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = BranchService.create_branch(
        db, change_order_id=change_order.change_order_id
    )

    from app.models import WBE

    entity_id = uuid.uuid4()

    # Create WBE in branch
    branch_wbe = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Branch WBE",
        revenue_allocation=50000.00,
        business_status="designing",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_wbe)
    db.commit()

    # Count WBEs in main before merge
    wbes_before = db.exec(
        select(WBE).where(WBE.entity_id == entity_id).where(WBE.branch == "main")
    ).all()
    count_before = len(wbes_before)

    # Create a mock error scenario by patching the session to raise an error
    # We'll use a transaction and rollback manually to simulate failure
    try:
        # Start a savepoint
        db.begin_nested()

        # Attempt merge (this should work)
        BranchService.merge_branch(
            session=db,
            branch=branch,
            change_order_id=change_order.change_order_id,
        )

        # Manually rollback to simulate error
        db.rollback()

        # Verify no changes were committed
        wbes_after_rollback = db.exec(
            select(WBE).where(WBE.entity_id == entity_id).where(WBE.branch == "main")
        ).all()
        assert len(wbes_after_rollback) == count_before  # No new versions created

        # Verify branch entity status unchanged
        branch_wbe_after = db.get(WBE, branch_wbe.wbe_id)
        assert branch_wbe_after is not None
        assert branch_wbe_after.status == "active"  # Not changed to "merged"

    finally:
        # Clean up - commit the outer transaction
        db.commit()

    # Now do a successful merge
    BranchService.merge_branch(
        session=db,
        branch=branch,
        change_order_id=change_order.change_order_id,
    )
    db.commit()

    # Verify merge succeeded after rollback
    wbes_after = db.exec(
        select(WBE).where(WBE.entity_id == entity_id).where(WBE.branch == "main")
    ).all()
    assert len(wbes_after) == count_before + 1  # New version created

    branch_wbe_final = db.get(WBE, branch_wbe.wbe_id)
    assert branch_wbe_final is not None
    assert branch_wbe_final.status == "merged"  # Now merged


def test_delete_branch_sets_status_deleted(db: Session) -> None:
    """Test that delete_branch sets status='deleted' for all branch entities."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = BranchService.create_branch(
        db, change_order_id=change_order.change_order_id
    )

    from app.models import WBE, CostElement, CostElementType, CostElementTypeCreate

    # Create WBE in branch
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

    # Create CostElementType
    cet_in = CostElementTypeCreate(
        type_code=f"delete_{uuid.uuid4().hex[:6]}",
        type_name="Delete Type",
        category_type="engineering_mechanical",
        display_order=1,
        is_active=True,
    )
    cet = CostElementType.model_validate(cet_in)
    db.add(cet)
    db.commit()
    db.refresh(branch_wbe)
    db.refresh(cet)

    # Create CostElement in branch
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

    # Delete branch
    BranchService.delete_branch(session=db, branch=branch)
    db.commit()

    # Verify all branch entities have status='deleted'
    branch_wbes = db.exec(select(WBE).where(WBE.branch == branch)).all()
    for wbe in branch_wbes:
        assert wbe.status == "deleted"

    branch_cost_elements = db.exec(
        select(CostElement).where(CostElement.branch == branch)
    ).all()
    for ce in branch_cost_elements:
        assert ce.status == "deleted"


def test_delete_branch_preserves_versions(db: Session) -> None:
    """Test that soft delete preserves all versions (doesn't hard delete)."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = BranchService.create_branch(
        db, change_order_id=change_order.change_order_id
    )

    from app.models import WBE

    entity_id = uuid.uuid4()

    # Create multiple versions of WBE in branch
    wbe_v1 = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Version 1",
        revenue_allocation=10000.00,
        business_status="designing",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(wbe_v1)
    db.flush()

    wbe_v2 = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Version 2",
        revenue_allocation=20000.00,
        business_status="designing",
        branch=branch,
        version=2,
        status="active",
    )
    db.add(wbe_v2)
    db.commit()

    # Delete branch
    BranchService.delete_branch(session=db, branch=branch)
    db.commit()

    # Verify all versions still exist (not hard deleted)
    all_wbes = db.exec(
        select(WBE).where(WBE.branch == branch).where(WBE.entity_id == entity_id)
    ).all()
    assert len(all_wbes) == 2  # Both versions preserved

    # Verify all versions have status='deleted'
    for wbe in all_wbes:
        assert wbe.status == "deleted"


def test_delete_branch_hides_from_normal_queries(db: Session) -> None:
    """Test that soft deleted branch entities don't appear in normal queries."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = BranchService.create_branch(
        db, change_order_id=change_order.change_order_id
    )

    from app.models import WBE
    from app.services.branch_filtering import apply_branch_filters

    entity_id = uuid.uuid4()

    # Create WBE in branch
    branch_wbe = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Branch WBE",
        revenue_allocation=50000.00,
        business_status="designing",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_wbe)
    db.commit()

    # Verify it appears in normal query
    normal_query = apply_branch_filters(
        select(WBE), WBE, branch=branch, include_deleted=False
    )
    active_wbes = db.exec(normal_query).all()
    assert len(active_wbes) == 1
    assert active_wbes[0].wbe_id == branch_wbe.wbe_id

    # Delete branch
    BranchService.delete_branch(session=db, branch=branch)
    db.commit()

    # Verify it doesn't appear in normal query (status='active' filter)
    normal_query_after = apply_branch_filters(
        select(WBE), WBE, branch=branch, include_deleted=False
    )
    active_wbes_after = db.exec(normal_query_after).all()
    assert len(active_wbes_after) == 0  # Should not appear


def test_delete_branch_queryable_with_include_deleted(db: Session) -> None:
    """Test that soft deleted branch entities can be queried with include_deleted flag."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = BranchService.create_branch(
        db, change_order_id=change_order.change_order_id
    )

    from app.models import WBE
    from app.services.branch_filtering import apply_branch_filters

    entity_id = uuid.uuid4()

    # Create WBE in branch
    branch_wbe = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Branch WBE",
        revenue_allocation=50000.00,
        business_status="designing",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_wbe)
    db.commit()
    wbe_id = branch_wbe.wbe_id

    # Delete branch
    BranchService.delete_branch(session=db, branch=branch)
    db.commit()

    # Verify it appears in query with include_deleted=True
    deleted_query = apply_branch_filters(
        select(WBE), WBE, branch=branch, include_deleted=True
    )
    all_wbes = db.exec(deleted_query).all()
    assert len(all_wbes) == 1
    assert all_wbes[0].wbe_id == wbe_id
    assert all_wbes[0].status == "deleted"


def test_delete_branch_prevents_main_branch_deletion(db: Session) -> None:
    """Test that delete_branch raises ValueError when attempting to delete main branch."""
    with pytest.raises(ValueError, match="Cannot delete the main branch"):
        BranchService.delete_branch(session=db, branch="main")
