"""Tests for version archival service."""

from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.models import Project, User, UserCreate
from app.services.version_archival_service import VersionArchivalService


def _create_pm_user(session: Session) -> User:
    """Helper to create a project manager user."""
    import uuid

    email = f"pm_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    from app import crud

    return crud.create_user(session=session, user_create=user_in)


def _create_project(session: Session, pm_user: User) -> Project:
    """Helper to create a project."""
    from datetime import date

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


def test_identify_versions_for_archival_finds_old_versions(db: Session) -> None:
    """Test that old versions are identified for archival."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)

    # Manually set created_at to be old
    from sqlalchemy import text

    old_date = datetime.utcnow() - timedelta(days=366)
    db.execute(
        text(
            "UPDATE project SET created_at = :old_date WHERE project_id = :project_id"
        ),
        {"old_date": old_date, "project_id": project.project_id},
    )
    db.commit()

    # Identify versions for archival with 365 day retention
    old_versions = VersionArchivalService.identify_versions_for_archival(
        session=db,
        entity_class=Project,
        retention_days=365,
    )

    assert len(old_versions) == 1
    assert old_versions[0].project_id == project.project_id


def test_archive_versions_marks_old_versions_as_archived(db: Session) -> None:
    """Test that archiving marks old versions as archived."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)

    # Create a second version
    from app.services.entity_versioning import update_entity_with_version

    update_entity_with_version(
        session=db,
        entity_class=Project,
        entity_id=project.project_id,
        update_data={"project_name": "Updated Project"},
        entity_type="project",
    )
    db.commit()

    # Make the first version old
    from sqlalchemy import text

    old_date = datetime.utcnow() - timedelta(days=366)
    db.execute(
        text(
            "UPDATE project SET created_at = :old_date WHERE project_id = :project_id AND version = 1"
        ),
        {"old_date": old_date, "project_id": project.project_id},
    )
    db.commit()

    # Archive versions
    archived_count = VersionArchivalService.archive_versions(
        session=db,
        entity_class=Project,
        retention_days=365,
    )

    assert archived_count == 1

    # Verify version 1 is archived
    archived = db.exec(
        select(Project)
        .where(Project.project_id == project.project_id)
        .where(Project.version == 1)
    ).first()
    assert archived is not None
    assert archived.status == "archived"


def test_archive_versions_preserves_latest_version(db: Session) -> None:
    """Test that archiving does not archive the latest version."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)

    # Create a second version
    from app.services.entity_versioning import update_entity_with_version

    update_entity_with_version(
        session=db,
        entity_class=Project,
        entity_id=project.project_id,
        update_data={"project_name": "Updated Project"},
        entity_type="project",
    )
    db.commit()

    # Make both versions old
    from sqlalchemy import text

    old_date = datetime.utcnow() - timedelta(days=366)
    db.execute(
        text(
            "UPDATE project SET created_at = :old_date WHERE project_id = :project_id"
        ),
        {"old_date": old_date, "project_id": project.project_id},
    )
    db.commit()

    # Archive versions
    archived_count = VersionArchivalService.archive_versions(
        session=db,
        entity_class=Project,
        retention_days=365,
    )

    # Should only archive version 1, not version 2 (latest)
    assert archived_count == 1

    # Verify version 2 (latest) is not archived
    latest = db.exec(
        select(Project)
        .where(Project.project_id == project.project_id)
        .where(Project.version == 2)
    ).first()
    assert latest is not None
    assert latest.status != "archived"


def test_restore_archived_version(db: Session) -> None:
    """Test that archived versions can be restored."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)

    # Manually set status to archived
    from sqlalchemy import text

    db.execute(
        text("UPDATE project SET status = 'archived' WHERE project_id = :project_id"),
        {"project_id": project.project_id},
    )
    db.commit()

    # Restore the archived version
    restored = VersionArchivalService.restore_archived_version(
        session=db,
        entity_class=Project,
        entity_id=project.entity_id,
        version=project.version,
    )

    assert restored is not None
    assert restored.status == "active"
