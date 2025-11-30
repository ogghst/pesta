"""Tests for BaselineWBE model."""
import uuid
from datetime import date
from decimal import Decimal

from sqlmodel import Session

from app import crud
from app.models import (
    WBE,
    BaselineLog,
    BaselineLogCreate,
    BaselineWBE,
    BaselineWBECreate,
    Project,
    ProjectCreate,
    UserCreate,
    WBECreate,
)


def test_create_baseline_wbe(db: Session) -> None:
    """Test creating a baseline WBE entry."""
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

    # Create a WBE
    wbe_in = WBECreate(
        machine_type="Test Machine",
        project_id=project.project_id,
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

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

    # Create a baseline WBE
    baseline_wbe_in = BaselineWBECreate(
        baseline_id=baseline.baseline_id,
        wbe_id=wbe.wbe_id,
        planned_value=Decimal("50000.00"),
        earned_value=Decimal("45000.00"),
        actual_cost=Decimal("48000.00"),
        budget_bac=Decimal("100000.00"),
        eac=Decimal("105000.00"),
        forecasted_quality=Decimal("1.0000"),
        cpi=Decimal("0.9375"),
        spi=Decimal("0.9000"),
        tcpi=Decimal("1.1818"),
        cost_variance=Decimal("-3000.00"),
        schedule_variance=Decimal("-5000.00"),
    )

    baseline_wbe = BaselineWBE.model_validate(baseline_wbe_in)
    db.add(baseline_wbe)
    db.commit()
    db.refresh(baseline_wbe)

    # Verify baseline WBE was created
    assert baseline_wbe.baseline_wbe_id is not None
    assert baseline_wbe.baseline_id == baseline.baseline_id
    assert baseline_wbe.wbe_id == wbe.wbe_id
    assert baseline_wbe.planned_value == Decimal("50000.00")
    assert baseline_wbe.earned_value == Decimal("45000.00")
    assert baseline_wbe.actual_cost == Decimal("48000.00")
    assert baseline_wbe.budget_bac == Decimal("100000.00")
    assert baseline_wbe.eac == Decimal("105000.00")
    assert baseline_wbe.forecasted_quality == Decimal("1.0000")
    assert baseline_wbe.cpi == Decimal("0.9375")
    assert baseline_wbe.spi == Decimal("0.9000")
    assert baseline_wbe.tcpi == Decimal("1.1818")
    assert baseline_wbe.cost_variance == Decimal("-3000.00")
    assert baseline_wbe.schedule_variance == Decimal("-5000.00")
    assert hasattr(baseline_wbe, "baseline_log")  # Relationship should exist
    assert hasattr(baseline_wbe, "wbe")  # Relationship should exist
