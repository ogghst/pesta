"""Tests for retention policy service."""

from datetime import date, datetime, timedelta

from sqlmodel import Session, select

from app.models import Project, User, UserCreate
from app.services.entity_versioning import soft_delete_entity
from app.services.retention_policy_service import RetentionPolicyService


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


def test_identify_expired_entities_finds_old_deleted_projects(db: Session) -> None:
    """Test that expired entities are identified correctly."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)

    # Soft delete the project
    soft_delete_entity(
        session=db,
        entity_class=Project,
        entity_id=project.project_id,
        entity_type="project",
    )
    db.commit()

    # Manually set the created_at timestamp to be old (91 days ago)
    deleted_project = db.exec(
        select(Project).where(Project.status == "deleted")
    ).first()
    assert deleted_project is not None

    # Use SQL to update the created_at timestamp
    from sqlalchemy import text

    old_date = datetime.utcnow() - timedelta(days=91)
    db.execute(
        text(
            "UPDATE project SET created_at = :old_date WHERE project_id = :project_id"
        ),
        {"old_date": old_date, "project_id": project.project_id},
    )
    db.commit()

    # Identify expired entities with 90 day retention
    expired = RetentionPolicyService.identify_expired_entities(
        session=db,
        entity_class=Project,
        entity_type="project",
        retention_days=90,
    )

    assert len(expired) == 1
    assert expired[0].project_id == project.project_id
    assert expired[0].status == "deleted"


def test_identify_expired_entities_ignores_recent_deletions(db: Session) -> None:
    """Test that recently deleted entities are not identified as expired."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)

    # Soft delete the project
    soft_delete_entity(
        session=db,
        entity_class=Project,
        entity_id=project.project_id,
        entity_type="project",
    )
    db.commit()

    # Identify expired entities with 90 day retention
    expired = RetentionPolicyService.identify_expired_entities(
        session=db,
        entity_class=Project,
        entity_type="project",
        retention_days=90,
    )

    # Should not find anything since deletion was recent
    assert len(expired) == 0


def test_enforce_retention_policy_permanently_deletes_expired_entities(
    db: Session,
) -> None:
    """Test that enforcement permanently deletes expired entities."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)

    # Soft delete the project
    soft_delete_entity(
        session=db,
        entity_class=Project,
        entity_id=project.project_id,
        entity_type="project",
    )
    db.commit()

    # Manually set the created_at timestamp to be old
    from sqlalchemy import text

    old_date = datetime.utcnow() - timedelta(days=91)
    db.execute(
        text(
            "UPDATE project SET created_at = :old_date WHERE project_id = :project_id"
        ),
        {"old_date": old_date, "project_id": project.project_id},
    )
    db.commit()

    # Enforce retention policy
    deleted_count = RetentionPolicyService.enforce_retention_policy(
        session=db,
        entity_class=Project,
        entity_type="project",
        retention_days=90,
    )

    assert deleted_count == 1

    # Verify entity is permanently deleted
    all_versions = db.exec(
        select(Project).where(Project.entity_id == project.entity_id)
    ).all()
    assert len(all_versions) == 0


def test_enforce_retention_policy_respects_retention_period(db: Session) -> None:
    """Test that enforcement respects the retention period."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)

    # Soft delete the project
    soft_delete_entity(
        session=db,
        entity_class=Project,
        entity_id=project.project_id,
        entity_type="project",
    )
    db.commit()

    # Enforce retention policy with long retention period
    deleted_count = RetentionPolicyService.enforce_retention_policy(
        session=db,
        entity_class=Project,
        entity_type="project",
        retention_days=365,
    )

    # Should not delete anything since retention period is long
    assert deleted_count == 0

    # Verify entity still exists (soft deleted)
    deleted_project = db.exec(
        select(Project).where(Project.status == "deleted")
    ).first()
    assert deleted_project is not None
