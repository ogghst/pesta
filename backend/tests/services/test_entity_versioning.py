"""Tests for entity versioning utilities."""

import uuid

from sqlmodel import Session

from app.models import WBE, CostElement
from app.services.entity_versioning import ensure_branch_version
from tests.utils.cost_element import create_random_cost_element
from tests.utils.wbe import create_random_wbe


def test_ensure_branch_version_wbe_exists_in_branch(db: Session) -> None:
    """Test that ensure_branch_version returns existing entity if it exists in branch."""
    # Create WBE in a branch
    wbe = create_random_wbe(db)
    entity_id = wbe.entity_id

    # Create a version in a different branch
    from app.services.version_service import VersionService

    next_version = VersionService.get_next_version(
        session=db, entity_type="wbe", entity_id=entity_id, branch="co-001"
    )

    branch_wbe = WBE(
        entity_id=entity_id,
        project_id=wbe.project_id,
        machine_type=wbe.machine_type,
        serial_number=wbe.serial_number,
        contracted_delivery_date=wbe.contracted_delivery_date,
        revenue_allocation=wbe.revenue_allocation,
        business_status=wbe.business_status,
        notes=wbe.notes,
        version=next_version,
        status="active",
        branch="co-001",
    )
    db.add(branch_wbe)
    db.commit()
    db.refresh(branch_wbe)

    # Ensure branch version should return the existing branch entity
    result = ensure_branch_version(db, WBE, entity_id, "co-001", "wbe")

    assert result is not None
    assert result.entity_id == entity_id
    assert result.branch == "co-001"
    assert result.wbe_id == branch_wbe.wbe_id


def test_ensure_branch_version_wbe_creates_from_main(db: Session) -> None:
    """Test that ensure_branch_version creates version 1 in branch if only exists in main."""
    # Create WBE in main branch
    wbe = create_random_wbe(db)
    entity_id = wbe.entity_id

    # Ensure branch version should create a copy in the branch
    result = ensure_branch_version(db, WBE, entity_id, "co-001", "wbe")

    assert result is not None
    assert result.entity_id == entity_id
    assert result.branch == "co-001"
    assert result.version == 1
    assert result.status == "active"
    assert result.machine_type == wbe.machine_type
    assert result.revenue_allocation == wbe.revenue_allocation


def test_ensure_branch_version_wbe_not_found(db: Session) -> None:
    """Test that ensure_branch_version raises ValueError if entity not found in any branch."""
    non_existent_id = uuid.uuid4()

    # Should raise ValueError
    try:
        ensure_branch_version(db, WBE, non_existent_id, "co-001", "wbe")
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "not found" in str(e).lower()


def test_ensure_branch_version_wbe_main_branch_error(db: Session) -> None:
    """Test that ensure_branch_version raises ValueError if branch is 'main'."""
    wbe = create_random_wbe(db)
    entity_id = wbe.entity_id

    # Should raise ValueError for main branch
    try:
        ensure_branch_version(db, WBE, entity_id, "main", "wbe")
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "main" in str(e).lower()


def test_ensure_branch_version_cost_element_exists_in_branch(db: Session) -> None:
    """Test that ensure_branch_version returns existing CostElement if it exists in branch."""
    # Create CostElement in main branch
    ce = create_random_cost_element(db)
    entity_id = ce.entity_id

    # Create a version in a different branch
    from app.services.version_service import VersionService

    next_version = VersionService.get_next_version(
        session=db, entity_type="costelement", entity_id=entity_id, branch="co-001"
    )

    branch_ce = CostElement(
        entity_id=entity_id,
        wbe_id=ce.wbe_id,
        cost_element_type_id=ce.cost_element_type_id,
        department_code=ce.department_code,
        department_name=ce.department_name,
        budget_bac=ce.budget_bac,
        revenue_plan=ce.revenue_plan,
        business_status=ce.business_status,
        notes=ce.notes,
        version=next_version,
        status="active",
        branch="co-001",
    )
    db.add(branch_ce)
    db.commit()
    db.refresh(branch_ce)

    # Ensure branch version should return the existing branch entity
    result = ensure_branch_version(db, CostElement, entity_id, "co-001", "costelement")

    assert result is not None
    assert result.entity_id == entity_id
    assert result.branch == "co-001"
    assert result.cost_element_id == branch_ce.cost_element_id


def test_ensure_branch_version_cost_element_creates_from_main(db: Session) -> None:
    """Test that ensure_branch_version creates version 1 CostElement in branch if only exists in main."""
    # Create CostElement in main branch
    ce = create_random_cost_element(db)
    entity_id = ce.entity_id

    # Ensure branch version should create a copy in the branch
    result = ensure_branch_version(db, CostElement, entity_id, "co-001", "costelement")

    assert result is not None
    assert result.entity_id == entity_id
    assert result.branch == "co-001"
    assert result.version == 1
    assert result.status == "active"
    assert result.department_code == ce.department_code
    assert result.budget_bac == ce.budget_bac
