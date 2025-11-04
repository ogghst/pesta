"""Tests for BaselineLog model."""
import uuid
from datetime import date

from sqlmodel import Session

from app import crud
from app.models import (
    BaselineLog,
    BaselineLogCreate,
    BaselineLogPublic,
    Project,
    ProjectCreate,
    UserCreate,
)


def test_create_baseline_log(db: Session) -> None:
    """Test creating a baseline log entry."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Test Project",
        customer_name="Test Customer",
        contract_value=100000.00,
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
        description="Initial schedule baseline",
        project_id=project.project_id,
        created_by_id=user.id,
    )

    baseline = BaselineLog.model_validate(baseline_in)
    db.add(baseline)
    db.commit()
    db.refresh(baseline)

    # Verify baseline was created
    assert baseline.baseline_id is not None
    assert baseline.baseline_type == "schedule"
    assert baseline.baseline_date == date(2024, 1, 15)
    assert baseline.milestone_type == "kickoff"
    assert baseline.description == "Initial schedule baseline"
    assert baseline.is_cancelled is False  # Default value
    assert baseline.project_id == project.project_id
    assert baseline.created_by_id == user.id
    assert hasattr(baseline, "created_by")  # Relationship should exist
    assert hasattr(baseline, "project")  # Relationship should exist


def test_baseline_type_enum(db: Session) -> None:
    """Test that baseline_type is validated."""
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Test Project",
        customer_name="Test Customer",
        contract_value=100000.00,
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Test valid types
    valid_types = ["schedule", "earned_value", "budget", "forecast", "combined"]
    for baseline_type in valid_types:
        baseline_in = BaselineLogCreate(
            baseline_type=baseline_type,
            baseline_date=date(2024, 1, 15),
            milestone_type="kickoff",
            project_id=project.project_id,
            created_by_id=user.id,
        )
        baseline = BaselineLog.model_validate(baseline_in)
        db.add(baseline)
        db.commit()
        db.refresh(baseline)
        assert baseline.baseline_type == baseline_type


def test_baseline_user_relationship(db: Session) -> None:
    """Test that baseline log references user correctly."""
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Test Project",
        customer_name="Test Customer",
        contract_value=100000.00,
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

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

    assert baseline.created_by_id == user.id
    assert baseline.project_id == project.project_id


def test_baseline_log_public_schema() -> None:
    """Test BaselineLogPublic schema for API responses."""
    import datetime

    baseline_id = uuid.uuid4()
    project_id = uuid.uuid4()
    user_id = uuid.uuid4()
    now = datetime.datetime.now(datetime.timezone.utc)

    baseline_public = BaselineLogPublic(
        baseline_id=baseline_id,
        baseline_type="earned_value",
        baseline_date=date(2024, 3, 1),
        milestone_type="engineering_complete",
        description="Public test baseline",
        is_cancelled=False,
        project_id=project_id,
        created_by_id=user_id,
        created_at=now,
    )

    assert baseline_public.baseline_id == baseline_id
    assert baseline_public.baseline_type == "earned_value"
    assert baseline_public.milestone_type == "engineering_complete"
    assert baseline_public.is_cancelled is False
    assert baseline_public.project_id == project_id
    assert baseline_public.created_by_id == user_id
    assert baseline_public.created_at == now


def test_baseline_log_is_cancelled_default(db: Session) -> None:
    """Test that is_cancelled defaults to False."""
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Test Project",
        customer_name="Test Customer",
        contract_value=100000.00,
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

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

    assert baseline.is_cancelled is False


def test_baseline_log_milestone_type_enum(db: Session) -> None:
    """Test that milestone_type is validated."""
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project_in = ProjectCreate(
        project_name="Test Project",
        customer_name="Test Customer",
        contract_value=100000.00,
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=user.id,
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Test valid milestone types
    valid_milestones = [
        "kickoff",
        "bom_release",
        "engineering_complete",
        "procurement_complete",
        "manufacturing_start",
        "shipment",
        "site_arrival",
        "commissioning_start",
        "commissioning_complete",
        "closeout",
    ]
    for milestone_type in valid_milestones:
        baseline_in = BaselineLogCreate(
            baseline_type="schedule",
            baseline_date=date(2024, 1, 15),
            milestone_type=milestone_type,
            project_id=project.project_id,
            created_by_id=user.id,
        )
        baseline = BaselineLog.model_validate(baseline_in)
        db.add(baseline)
        db.commit()
        db.refresh(baseline)
        assert baseline.milestone_type == milestone_type
