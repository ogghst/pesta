"""Tests for merged view service."""

import uuid
from datetime import date
from decimal import Decimal

from sqlmodel import Session

from app.models import WBE, Project, ProjectCreate, User, UserCreate
from app.services.merged_view_service import MergedViewService


def _create_pm_user(session: Session) -> User:
    """Helper to create a project manager user."""
    email = f"pm_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    from app import crud

    return crud.create_user(session=session, user_create=user_in)


def _create_project(session: Session, pm_user: User) -> Project:
    """Helper to create a project."""
    project_in = ProjectCreate(
        project_name="Merged View Test Project",
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


def test_get_merged_wbes_returns_all_main_and_branch_entities(db: Session) -> None:
    """Test that get_merged_wbes returns all main branch WBEs + branch WBEs."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    branch = "co-001"

    # Create WBEs in main branch
    main_wbe1 = WBE(
        entity_id=uuid.uuid4(),
        project_id=project.project_id,
        machine_type="Main WBE 1",
        revenue_allocation=Decimal("10000.00"),
        business_status="designing",
        branch="main",
        version=1,
        status="active",
    )
    main_wbe2 = WBE(
        entity_id=uuid.uuid4(),
        project_id=project.project_id,
        machine_type="Main WBE 2",
        revenue_allocation=Decimal("20000.00"),
        business_status="designing",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_wbe1)
    db.add(main_wbe2)
    db.flush()

    # Create WBE in branch
    branch_wbe = WBE(
        entity_id=uuid.uuid4(),
        project_id=project.project_id,
        machine_type="Branch WBE",
        revenue_allocation=Decimal("30000.00"),
        business_status="designing",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_wbe)
    db.commit()

    # Get merged view
    merged_wbes = MergedViewService.get_merged_wbes(
        session=db, project_id=project.project_id, branch=branch
    )

    # Should return all 3 WBEs (2 main + 1 branch)
    assert len(merged_wbes) == 3

    # Check that all entities are present
    entity_ids = {wbe["entity"].entity_id for wbe in merged_wbes}
    assert main_wbe1.entity_id in entity_ids
    assert main_wbe2.entity_id in entity_ids
    assert branch_wbe.entity_id in entity_ids


def test_get_merged_wbes_marks_entities_with_change_status(db: Session) -> None:
    """Test that get_merged_wbes marks entities with correct change status."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    branch = "co-001"

    entity_id_main = uuid.uuid4()
    entity_id_branch = uuid.uuid4()
    entity_id_updated = uuid.uuid4()
    entity_id_deleted = uuid.uuid4()

    # Create WBE in main only (unchanged)
    main_only = WBE(
        entity_id=entity_id_main,
        project_id=project.project_id,
        machine_type="Main Only",
        revenue_allocation=Decimal("10000.00"),
        business_status="designing",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_only)
    db.flush()

    # Create WBE in branch only (created)
    branch_only = WBE(
        entity_id=entity_id_branch,
        project_id=project.project_id,
        machine_type="Branch Only",
        revenue_allocation=Decimal("20000.00"),
        business_status="designing",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_only)
    db.flush()

    # Create WBE in both (updated in branch)
    main_updated = WBE(
        entity_id=entity_id_updated,
        project_id=project.project_id,
        machine_type="Original",
        revenue_allocation=Decimal("10000.00"),
        business_status="designing",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_updated)
    db.flush()

    branch_updated = WBE(
        entity_id=entity_id_updated,
        project_id=project.project_id,
        machine_type="Updated",
        revenue_allocation=Decimal("15000.00"),  # Different value
        business_status="designing",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_updated)
    db.flush()

    # Create WBE deleted in branch
    main_deleted = WBE(
        entity_id=entity_id_deleted,
        project_id=project.project_id,
        machine_type="To Be Deleted",
        revenue_allocation=Decimal("5000.00"),
        business_status="designing",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_deleted)
    db.flush()

    branch_deleted = WBE(
        entity_id=entity_id_deleted,
        project_id=project.project_id,
        machine_type="To Be Deleted",
        revenue_allocation=Decimal("5000.00"),
        business_status="designing",
        branch=branch,
        version=1,
        status="deleted",  # Deleted in branch
    )
    db.add(branch_deleted)
    db.commit()

    # Get merged view
    merged_wbes = MergedViewService.get_merged_wbes(
        session=db, project_id=project.project_id, branch=branch
    )

    # Find entities by entity_id
    merged_map = {wbe["entity"].entity_id: wbe for wbe in merged_wbes}

    # Check change statuses
    assert merged_map[entity_id_main]["change_status"] == "unchanged"
    assert merged_map[entity_id_branch]["change_status"] == "created"
    assert merged_map[entity_id_updated]["change_status"] == "updated"
    assert merged_map[entity_id_deleted]["change_status"] == "deleted"


def test_get_merged_wbes_uses_branch_comparison_api(db: Session) -> None:
    """Test that get_merged_wbes uses branch comparison API to determine change status."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    branch = "co-001"

    entity_id = uuid.uuid4()

    # Create WBE in main
    main_wbe = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Main WBE",
        revenue_allocation=Decimal("10000.00"),
        business_status="designing",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_wbe)
    db.flush()

    # Create modified WBE in branch
    branch_wbe = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Modified WBE",
        revenue_allocation=Decimal("20000.00"),  # Different
        business_status="designing",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_wbe)
    db.commit()

    # Get merged view
    merged_wbes = MergedViewService.get_merged_wbes(
        session=db, project_id=project.project_id, branch=branch
    )

    # Should use comparison logic to detect update
    merged_map = {wbe["entity"].entity_id: wbe for wbe in merged_wbes}
    assert merged_map[entity_id]["change_status"] == "updated"


def test_get_merged_wbes_returns_latest_active_version_per_branch(db: Session) -> None:
    """Test that get_merged_wbes returns latest active version per branch."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    branch = "co-001"

    entity_id = uuid.uuid4()

    # Create multiple versions in main branch
    main_v1 = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Main v1",
        revenue_allocation=Decimal("10000.00"),
        business_status="designing",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_v1)
    db.flush()

    main_v2 = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Main v2",
        revenue_allocation=Decimal("15000.00"),
        business_status="designing",
        branch="main",
        version=2,
        status="active",  # Latest active version
    )
    db.add(main_v2)
    db.flush()

    main_v3 = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Main v3",
        revenue_allocation=Decimal("20000.00"),
        business_status="designing",
        branch="main",
        version=3,
        status="deleted",  # Not active
    )
    db.add(main_v3)
    db.commit()

    # Get merged view
    merged_wbes = MergedViewService.get_merged_wbes(
        session=db, project_id=project.project_id, branch=branch
    )

    # Should return version 2 (latest active)
    merged_map = {wbe["entity"].entity_id: wbe for wbe in merged_wbes}
    assert merged_map[entity_id]["entity"].version == 2
    assert merged_map[entity_id]["entity"].machine_type == "Main v2"


def test_get_merged_wbes_includes_deleted_entities(db: Session) -> None:
    """Test that get_merged_wbes includes deleted entities with deleted status."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    branch = "co-001"

    entity_id = uuid.uuid4()

    # Create WBE in main
    main_wbe = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Main WBE",
        revenue_allocation=Decimal("10000.00"),
        business_status="designing",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_wbe)
    db.flush()

    # Create deleted version in branch
    branch_deleted = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Main WBE",
        revenue_allocation=Decimal("10000.00"),
        business_status="designing",
        branch=branch,
        version=1,
        status="deleted",  # Deleted in branch
    )
    db.add(branch_deleted)
    db.commit()

    # Get merged view
    merged_wbes = MergedViewService.get_merged_wbes(
        session=db, project_id=project.project_id, branch=branch
    )

    # Should include deleted entity
    merged_map = {wbe["entity"].entity_id: wbe for wbe in merged_wbes}
    assert entity_id in merged_map
    assert merged_map[entity_id]["change_status"] == "deleted"
    assert merged_map[entity_id]["entity"].status == "deleted"


def test_get_merged_wbes_handles_empty_branches(db: Session) -> None:
    """Test that get_merged_wbes handles empty branches correctly."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    branch = "co-001"

    # Create WBE only in main
    main_wbe = WBE(
        entity_id=uuid.uuid4(),
        project_id=project.project_id,
        machine_type="Main Only",
        revenue_allocation=Decimal("10000.00"),
        business_status="designing",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_wbe)
    db.commit()

    # Get merged view (branch is empty)
    merged_wbes = MergedViewService.get_merged_wbes(
        session=db, project_id=project.project_id, branch=branch
    )

    # Should return main WBE with unchanged status
    assert len(merged_wbes) == 1
    assert merged_wbes[0]["entity"].entity_id == main_wbe.entity_id
    assert merged_wbes[0]["change_status"] == "unchanged"

    # Test with empty main branch
    project2 = _create_project(db, pm_user)
    branch2 = "co-002"

    # Create WBE only in branch
    branch_wbe = WBE(
        entity_id=uuid.uuid4(),
        project_id=project2.project_id,
        machine_type="Branch Only",
        revenue_allocation=Decimal("20000.00"),
        business_status="designing",
        branch=branch2,
        version=1,
        status="active",
    )
    db.add(branch_wbe)
    db.commit()

    # Get merged view (main is empty)
    merged_wbes2 = MergedViewService.get_merged_wbes(
        session=db, project_id=project2.project_id, branch=branch2
    )

    # Should return branch WBE with created status
    assert len(merged_wbes2) == 1
    assert merged_wbes2[0]["entity"].entity_id == branch_wbe.entity_id
    assert merged_wbes2[0]["change_status"] == "created"


# ============================================================================
# Cost Element Merged View Tests
# ============================================================================


def test_get_merged_cost_elements_returns_all_main_and_branch_entities(
    db: Session,
) -> None:
    """Test that get_merged_cost_elements returns all main branch cost elements + branch cost elements."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    branch = "co-001"

    from app.models import CostElement, CostElementType, CostElementTypeCreate

    # Create WBE in main
    main_wbe = WBE(
        entity_id=uuid.uuid4(),
        project_id=project.project_id,
        machine_type="Main WBE",
        revenue_allocation=Decimal("10000.00"),
        business_status="designing",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_wbe)
    db.flush()

    # Create CostElementType
    cet_in = CostElementTypeCreate(
        type_code=f"test_{uuid.uuid4().hex[:6]}",
        type_name="Test Type",
        category_type="engineering_mechanical",
        display_order=1,
        is_active=True,
    )
    cet = CostElementType.model_validate(cet_in)
    db.add(cet)
    db.commit()
    db.refresh(main_wbe)
    db.refresh(cet)

    # Create cost elements in main branch
    main_ce1 = CostElement(
        entity_id=uuid.uuid4(),
        wbe_id=main_wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="MAIN1",
        department_name="Main Department 1",
        budget_bac=Decimal("10000.00"),
        revenue_plan=Decimal("12000.00"),
        business_status="planned",
        branch="main",
        version=1,
        status="active",
    )
    main_ce2 = CostElement(
        entity_id=uuid.uuid4(),
        wbe_id=main_wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="MAIN2",
        department_name="Main Department 2",
        budget_bac=Decimal("20000.00"),
        revenue_plan=Decimal("24000.00"),
        business_status="planned",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_ce1)
    db.add(main_ce2)
    db.flush()

    # Create WBE in branch
    branch_wbe = WBE(
        entity_id=uuid.uuid4(),
        project_id=project.project_id,
        machine_type="Branch WBE",
        revenue_allocation=Decimal("30000.00"),
        business_status="designing",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_wbe)
    db.flush()

    # Create cost element in branch
    branch_ce = CostElement(
        entity_id=uuid.uuid4(),
        wbe_id=branch_wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="BRANCH1",
        department_name="Branch Department",
        budget_bac=Decimal("30000.00"),
        revenue_plan=Decimal("36000.00"),
        business_status="planned",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_ce)
    db.commit()

    # Get merged view
    merged_ces = MergedViewService.get_merged_cost_elements(
        session=db, project_id=project.project_id, branch=branch
    )

    # Should return all 3 cost elements (2 main + 1 branch)
    assert len(merged_ces) == 3

    # Check that all entities are present
    entity_ids = {ce["entity"].entity_id for ce in merged_ces}
    assert main_ce1.entity_id in entity_ids
    assert main_ce2.entity_id in entity_ids
    assert branch_ce.entity_id in entity_ids


def test_get_merged_cost_elements_marks_entities_with_change_status(
    db: Session,
) -> None:
    """Test that get_merged_cost_elements marks entities with correct change status."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    branch = "co-001"

    from app.models import CostElement, CostElementType, CostElementTypeCreate

    # Create WBE in main
    main_wbe = WBE(
        entity_id=uuid.uuid4(),
        project_id=project.project_id,
        machine_type="Main WBE",
        revenue_allocation=Decimal("10000.00"),
        business_status="designing",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_wbe)
    db.flush()

    # Create CostElementType
    cet_in = CostElementTypeCreate(
        type_code=f"test_{uuid.uuid4().hex[:6]}",
        type_name="Test Type",
        category_type="engineering_mechanical",
        display_order=1,
        is_active=True,
    )
    cet = CostElementType.model_validate(cet_in)
    db.add(cet)
    db.commit()
    db.refresh(main_wbe)
    db.refresh(cet)

    entity_id_main = uuid.uuid4()
    entity_id_branch = uuid.uuid4()
    entity_id_updated = uuid.uuid4()
    entity_id_deleted = uuid.uuid4()

    # Create cost element in main only (unchanged)
    main_only = CostElement(
        entity_id=entity_id_main,
        wbe_id=main_wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="MAIN",
        department_name="Main Only",
        budget_bac=Decimal("10000.00"),
        revenue_plan=Decimal("12000.00"),
        business_status="planned",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_only)
    db.flush()

    # Create WBE in branch
    branch_wbe = WBE(
        entity_id=uuid.uuid4(),
        project_id=project.project_id,
        machine_type="Branch WBE",
        revenue_allocation=Decimal("20000.00"),
        business_status="designing",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_wbe)
    db.flush()

    # Create cost element in branch only (created)
    branch_only = CostElement(
        entity_id=entity_id_branch,
        wbe_id=branch_wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="BRANCH",
        department_name="Branch Only",
        budget_bac=Decimal("20000.00"),
        revenue_plan=Decimal("24000.00"),
        business_status="planned",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_only)
    db.flush()

    # Create cost element in both (updated in branch)
    main_updated = CostElement(
        entity_id=entity_id_updated,
        wbe_id=main_wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="ORIG",
        department_name="Original",
        budget_bac=Decimal("10000.00"),
        revenue_plan=Decimal("12000.00"),
        business_status="planned",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_updated)
    db.flush()

    branch_updated = CostElement(
        entity_id=entity_id_updated,
        wbe_id=branch_wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="UPD",
        department_name="Updated",
        budget_bac=Decimal("15000.00"),  # Different
        revenue_plan=Decimal("18000.00"),  # Different
        business_status="planned",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_updated)
    db.flush()

    # Create cost element deleted in branch
    main_deleted = CostElement(
        entity_id=entity_id_deleted,
        wbe_id=main_wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="DEL",
        department_name="To Be Deleted",
        budget_bac=Decimal("5000.00"),
        revenue_plan=Decimal("6000.00"),
        business_status="planned",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_deleted)
    db.flush()

    branch_deleted = CostElement(
        entity_id=entity_id_deleted,
        wbe_id=branch_wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="DEL",
        department_name="To Be Deleted",
        budget_bac=Decimal("5000.00"),
        revenue_plan=Decimal("6000.00"),
        business_status="planned",
        branch=branch,
        version=1,
        status="deleted",  # Deleted in branch
    )
    db.add(branch_deleted)
    db.commit()

    # Get merged view
    merged_ces = MergedViewService.get_merged_cost_elements(
        session=db, project_id=project.project_id, branch=branch
    )

    # Find entities by entity_id
    merged_map = {ce["entity"].entity_id: ce for ce in merged_ces}

    # Check change statuses
    assert merged_map[entity_id_main]["change_status"] == "unchanged"
    assert merged_map[entity_id_branch]["change_status"] == "created"
    assert merged_map[entity_id_updated]["change_status"] == "updated"
    assert merged_map[entity_id_deleted]["change_status"] == "deleted"


def test_get_merged_cost_elements_handles_cost_elements_within_wbes_correctly(
    db: Session,
) -> None:
    """Test that get_merged_cost_elements handles cost elements within WBEs correctly."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    branch = "co-001"

    from app.models import CostElement, CostElementType, CostElementTypeCreate

    # Create WBE in main
    main_wbe = WBE(
        entity_id=uuid.uuid4(),
        project_id=project.project_id,
        machine_type="Main WBE",
        revenue_allocation=Decimal("10000.00"),
        business_status="designing",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_wbe)
    db.flush()

    # Create CostElementType
    cet_in = CostElementTypeCreate(
        type_code=f"test_{uuid.uuid4().hex[:6]}",
        type_name="Test Type",
        category_type="engineering_mechanical",
        display_order=1,
        is_active=True,
    )
    cet = CostElementType.model_validate(cet_in)
    db.add(cet)
    db.commit()
    db.refresh(main_wbe)
    db.refresh(cet)

    # Create cost element in main
    main_ce = CostElement(
        entity_id=uuid.uuid4(),
        wbe_id=main_wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="MAIN",
        department_name="Main Department",
        budget_bac=Decimal("10000.00"),
        revenue_plan=Decimal("12000.00"),
        business_status="planned",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_ce)
    db.commit()

    # Get merged view
    merged_ces = MergedViewService.get_merged_cost_elements(
        session=db, project_id=project.project_id, branch=branch
    )

    # Should return main cost element with unchanged status
    assert len(merged_ces) == 1
    assert merged_ces[0]["entity"].entity_id == main_ce.entity_id
    assert merged_ces[0]["change_status"] == "unchanged"


def test_get_merged_cost_elements_includes_deleted_entities(db: Session) -> None:
    """Test that get_merged_cost_elements includes deleted entities with deleted status."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    branch = "co-001"

    from app.models import CostElement, CostElementType, CostElementTypeCreate

    # Create WBE in main
    main_wbe = WBE(
        entity_id=uuid.uuid4(),
        project_id=project.project_id,
        machine_type="Main WBE",
        revenue_allocation=Decimal("10000.00"),
        business_status="designing",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_wbe)
    db.flush()

    # Create CostElementType
    cet_in = CostElementTypeCreate(
        type_code=f"test_{uuid.uuid4().hex[:6]}",
        type_name="Test Type",
        category_type="engineering_mechanical",
        display_order=1,
        is_active=True,
    )
    cet = CostElementType.model_validate(cet_in)
    db.add(cet)
    db.commit()
    db.refresh(main_wbe)
    db.refresh(cet)

    entity_id = uuid.uuid4()

    # Create cost element in main
    main_ce = CostElement(
        entity_id=entity_id,
        wbe_id=main_wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="MAIN",
        department_name="Main Department",
        budget_bac=Decimal("10000.00"),
        revenue_plan=Decimal("12000.00"),
        business_status="planned",
        branch="main",
        version=1,
        status="active",
    )
    db.add(main_ce)
    db.flush()

    # Create WBE in branch
    branch_wbe = WBE(
        entity_id=uuid.uuid4(),
        project_id=project.project_id,
        machine_type="Branch WBE",
        revenue_allocation=Decimal("20000.00"),
        business_status="designing",
        branch=branch,
        version=1,
        status="active",
    )
    db.add(branch_wbe)
    db.flush()

    # Create deleted version in branch
    branch_deleted = CostElement(
        entity_id=entity_id,
        wbe_id=branch_wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="MAIN",
        department_name="Main Department",
        budget_bac=Decimal("10000.00"),
        revenue_plan=Decimal("12000.00"),
        business_status="planned",
        branch=branch,
        version=1,
        status="deleted",  # Deleted in branch
    )
    db.add(branch_deleted)
    db.commit()

    # Get merged view
    merged_ces = MergedViewService.get_merged_cost_elements(
        session=db, project_id=project.project_id, branch=branch
    )

    # Should include deleted entity
    merged_map = {ce["entity"].entity_id: ce for ce in merged_ces}
    assert entity_id in merged_map
    assert merged_map[entity_id]["change_status"] == "deleted"
    assert merged_map[entity_id]["entity"].status == "deleted"
