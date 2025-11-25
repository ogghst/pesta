"""Tests for version service."""

import uuid
from datetime import date

from sqlmodel import Session

from app import crud
from app.models import (
    WBE,
    Project,
    ProjectCreate,
    UserCreate,
)
from app.services.version_service import VersionService


def _create_project(db: Session) -> Project:
    """Helper to create a project with unique user."""
    email = f"pm_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    pm_user = crud.create_user(session=db, user_create=user_in)

    project_in = ProjectCreate(
        project_name="Version Service Project",
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
    return project


def _create_wbe(
    db: Session,
    *,
    entity_id: uuid.UUID,
    branch: str = "main",
    version: int = 1,
) -> WBE:
    """Helper to create a WBE record with specified branch/version."""
    project = _create_project(db)
    wbe = WBE(
        entity_id=entity_id,
        project_id=project.project_id,
        machine_type="Test WBE",
        revenue_allocation=10000.0,
        business_status="designing",
        branch=branch,
        version=version,
        status="active",
    )
    db.add(wbe)
    db.commit()
    db.refresh(wbe)
    return wbe


def test_get_next_version_new_entity(db: Session) -> None:
    """Test that get_next_version returns 1 for a new entity."""
    entity_id = uuid.uuid4()
    version = VersionService.get_next_version(
        session=db, entity_type="wbe", entity_id=entity_id, branch="main"
    )

    assert version == 1


def test_get_next_version_increments(db: Session) -> None:
    """Test that get_next_version increments correctly for same entity in same branch."""
    entity_id = uuid.uuid4()
    branch = "main"

    # Create initial WBE record (version=1)
    _create_wbe(db, entity_id=entity_id, branch=branch, version=1)

    # Next version should be 2
    version2 = VersionService.get_next_version(
        session=db, entity_type="wbe", entity_id=entity_id, branch=branch
    )
    assert version2 == 2

    # Simulate persisting new version by creating a new row with same entity_id
    _create_wbe(db, entity_id=entity_id, branch=branch, version=version2)

    # Third version should be 3
    version3 = VersionService.get_next_version(
        session=db, entity_type="wbe", entity_id=entity_id, branch=branch
    )
    assert version3 == 3


def test_get_next_version_per_branch(db: Session) -> None:
    """Test that version numbers are independent per branch."""
    entity_id = uuid.uuid4()

    # Version in main branch
    version_main = VersionService.get_next_version(
        session=db, entity_type="wbe", entity_id=entity_id, branch="main"
    )

    # Version in change order branch (should also start at 1)
    version_co = VersionService.get_next_version(
        session=db, entity_type="wbe", entity_id=entity_id, branch="co-001"
    )

    assert version_main == 1
    assert version_co == 1  # Independent sequence per branch


def test_get_current_version(db: Session) -> None:
    """Test that get_current_version returns active version for entity in branch."""
    entity_id = uuid.uuid4()
    branch = "main"

    # Create WBE with version 2
    wbe = _create_wbe(db, entity_id=entity_id, branch=branch, version=2)

    current_version = VersionService.get_current_version(
        session=db, entity_type="wbe", entity_id=entity_id, branch=branch
    )

    assert current_version == wbe.version


def test_get_next_version_cost_element(db: Session) -> None:
    """Test that get_next_version works for CostElement."""
    entity_id = uuid.uuid4()
    version = VersionService.get_next_version(
        session=db, entity_type="costelement", entity_id=entity_id, branch="main"
    )

    assert version == 1


def test_get_next_version_version_only_entity(db: Session) -> None:
    """Test that get_next_version works for version-only entities (no branch)."""
    entity_id = uuid.uuid4()
    version = VersionService.get_next_version(
        session=db,
        entity_type="project",
        entity_id=entity_id,
        branch=None,  # No branch for version-only entities
    )

    assert version == 1
