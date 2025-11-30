"""Tests for BaselineProject model."""
import uuid
from datetime import date
from decimal import Decimal

from sqlmodel import Session

from app import crud
from app.models import (
    BaselineLog,
    BaselineLogCreate,
    BaselineProject,
    BaselineProjectCreate,
    Project,
    ProjectCreate,
    UserCreate,
)


def test_create_baseline_project(db: Session) -> None:
    """Test creating a baseline project entry."""
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

    # Create a baseline project
    baseline_project_in = BaselineProjectCreate(
        baseline_id=baseline.baseline_id,
        project_id=project.project_id,
        planned_value=Decimal("200000.00"),
        earned_value=Decimal("180000.00"),
        actual_cost=Decimal("190000.00"),
        budget_bac=Decimal("250000.00"),
        eac=Decimal("260000.00"),
        forecasted_quality=Decimal("1.0000"),
        cpi=Decimal("0.9474"),
        spi=Decimal("0.9000"),
        tcpi=Decimal("1.1667"),
        cost_variance=Decimal("-10000.00"),
        schedule_variance=Decimal("-20000.00"),
    )

    baseline_project = BaselineProject.model_validate(baseline_project_in)
    db.add(baseline_project)
    db.commit()
    db.refresh(baseline_project)

    # Verify baseline project was created
    assert baseline_project.baseline_project_id is not None
    assert baseline_project.baseline_id == baseline.baseline_id
    assert baseline_project.project_id == project.project_id
    assert baseline_project.planned_value == Decimal("200000.00")
    assert baseline_project.earned_value == Decimal("180000.00")
    assert baseline_project.actual_cost == Decimal("190000.00")
    assert baseline_project.budget_bac == Decimal("250000.00")
    assert baseline_project.eac == Decimal("260000.00")
    assert baseline_project.forecasted_quality == Decimal("1.0000")
    assert baseline_project.cpi == Decimal("0.9474")
    assert baseline_project.spi == Decimal("0.9000")
    assert baseline_project.tcpi == Decimal("1.1667")
    assert baseline_project.cost_variance == Decimal("-10000.00")
    assert baseline_project.schedule_variance == Decimal("-20000.00")
    assert hasattr(baseline_project, "baseline_log")  # Relationship should exist
    assert hasattr(baseline_project, "project")  # Relationship should exist
