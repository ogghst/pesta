"""Tests for Baseline Snapshot API endpoints (WBE and Project levels)."""
import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.models import (
    BaselineProject,
    BaselineWBE,
    CostElementSchedule,
    CostRegistration,
    EarnedValueEntry,
    UserCreate,
)
from tests.utils.cost_element import create_random_cost_element
from tests.utils.project import create_random_project
from tests.utils.wbe import create_random_wbe


def test_create_baseline_creates_wbe_snapshots(
    db: Session, client: TestClient, superuser_token_headers: dict
) -> None:
    """Test that baseline creation creates WBE snapshots."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project = create_random_project(db, user.id)

    # Create two WBEs
    wbe1 = create_random_wbe(db, project.project_id)
    wbe2 = create_random_wbe(db, project.project_id)

    # Create cost elements for each WBE
    create_random_cost_element(db, wbe1.wbe_id)
    create_random_cost_element(db, wbe2.wbe_id)

    # Create a baseline
    baseline_data = {
        "baseline_type": "schedule",
        "baseline_date": "2024-06-15",
        "milestone_type": "kickoff",
        "description": "Test baseline with WBE snapshots",
    }
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/",
        headers=superuser_token_headers,
        json=baseline_data,
    )
    assert response.status_code == 200
    baseline = response.json()

    # Verify WBE snapshots were created
    wbe_snapshots = db.exec(
        select(BaselineWBE).where(BaselineWBE.baseline_id == baseline["baseline_id"])
    ).all()
    assert len(wbe_snapshots) == 2

    # Verify each WBE has a snapshot
    wbe_ids = {wbe1.wbe_id, wbe2.wbe_id}
    snapshot_wbe_ids = {snapshot.wbe_id for snapshot in wbe_snapshots}
    assert snapshot_wbe_ids == wbe_ids

    # Verify snapshots have metrics
    for snapshot in wbe_snapshots:
        assert snapshot.planned_value is not None
        assert snapshot.earned_value is not None
        assert snapshot.actual_cost is not None
        assert snapshot.budget_bac is not None
        assert snapshot.eac is not None


def test_create_baseline_creates_project_snapshot(
    db: Session, client: TestClient, superuser_token_headers: dict
) -> None:
    """Test that baseline creation creates project snapshot."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project = create_random_project(db, user.id)

    # Create WBEs and cost elements
    wbe = create_random_wbe(db, project.project_id)
    create_random_cost_element(db, wbe.wbe_id)

    # Create a baseline
    baseline_data = {
        "baseline_type": "schedule",
        "baseline_date": "2024-06-15",
        "milestone_type": "kickoff",
        "description": "Test baseline with project snapshot",
    }
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/",
        headers=superuser_token_headers,
        json=baseline_data,
    )
    assert response.status_code == 200
    baseline = response.json()

    # Verify project snapshot was created
    project_snapshot = db.exec(
        select(BaselineProject).where(
            BaselineProject.baseline_id == baseline["baseline_id"],
            BaselineProject.project_id == project.project_id,
        )
    ).first()
    assert project_snapshot is not None
    assert project_snapshot.planned_value is not None
    assert project_snapshot.earned_value is not None
    assert project_snapshot.actual_cost is not None
    assert project_snapshot.budget_bac is not None
    assert project_snapshot.eac is not None


def test_get_baseline_wbe_snapshots(
    db: Session, client: TestClient, superuser_token_headers: dict
) -> None:
    """Test getting all WBE snapshots for a baseline."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project = create_random_project(db, user.id)

    # Create WBEs
    wbe1 = create_random_wbe(db, project.project_id)
    wbe2 = create_random_wbe(db, project.project_id)

    # Create cost elements
    create_random_cost_element(db, wbe1.wbe_id)
    create_random_cost_element(db, wbe2.wbe_id)

    # Create a baseline
    baseline_data = {
        "baseline_type": "schedule",
        "baseline_date": "2024-06-15",
        "milestone_type": "kickoff",
        "description": "Test baseline",
    }
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/",
        headers=superuser_token_headers,
        json=baseline_data,
    )
    assert response.status_code == 200
    baseline = response.json()

    # Get WBE snapshots
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline['baseline_id']}/wbe-snapshots",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    snapshots = response.json()
    assert len(snapshots) == 2

    # Verify snapshot structure
    for snapshot in snapshots:
        assert "baseline_wbe_id" in snapshot
        assert "baseline_id" in snapshot
        assert "wbe_id" in snapshot
        assert "planned_value" in snapshot
        assert "earned_value" in snapshot
        assert "actual_cost" in snapshot
        assert "budget_bac" in snapshot
        assert "eac" in snapshot
        assert "cpi" in snapshot
        assert "spi" in snapshot
        assert "cost_variance" in snapshot
        assert "schedule_variance" in snapshot


def test_get_baseline_wbe_snapshot_detail(
    db: Session, client: TestClient, superuser_token_headers: dict
) -> None:
    """Test getting a specific WBE snapshot."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project = create_random_project(db, user.id)

    # Create WBE and cost element
    wbe = create_random_wbe(db, project.project_id)
    create_random_cost_element(db, wbe.wbe_id)

    # Create a baseline
    baseline_data = {
        "baseline_type": "schedule",
        "baseline_date": "2024-06-15",
        "milestone_type": "kickoff",
        "description": "Test baseline",
    }
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/",
        headers=superuser_token_headers,
        json=baseline_data,
    )
    assert response.status_code == 200
    baseline = response.json()

    # Get specific WBE snapshot
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline['baseline_id']}/wbe-snapshots/{wbe.wbe_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["wbe_id"] == str(wbe.wbe_id)
    assert snapshot["baseline_id"] == baseline["baseline_id"]


def test_get_baseline_project_snapshot(
    db: Session, client: TestClient, superuser_token_headers: dict
) -> None:
    """Test getting project snapshot."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project = create_random_project(db, user.id)

    # Create WBE and cost element
    wbe = create_random_wbe(db, project.project_id)
    create_random_cost_element(db, wbe.wbe_id)

    # Create a baseline
    baseline_data = {
        "baseline_type": "schedule",
        "baseline_date": "2024-06-15",
        "milestone_type": "kickoff",
        "description": "Test baseline",
    }
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/",
        headers=superuser_token_headers,
        json=baseline_data,
    )
    assert response.status_code == 200
    baseline = response.json()

    # Get project snapshot
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline['baseline_id']}/project-snapshot",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["project_id"] == str(project.project_id)
    assert snapshot["baseline_id"] == baseline["baseline_id"]
    assert "planned_value" in snapshot
    assert "earned_value" in snapshot
    assert "actual_cost" in snapshot
    assert "budget_bac" in snapshot
    assert "eac" in snapshot


def test_baseline_snapshot_metrics_accuracy(
    db: Session, client: TestClient, superuser_token_headers: dict
) -> None:
    """Test that baseline snapshot metrics match calculated values."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project = create_random_project(db, user.id)

    # Create WBE
    wbe = create_random_wbe(db, project.project_id)

    # Create cost element with known values
    cost_element = create_random_cost_element(db, wbe.wbe_id)
    cost_element.budget_bac = Decimal("100000.00")
    db.add(cost_element)
    db.commit()
    db.refresh(cost_element)

    # Create cost registration
    cost_reg = CostRegistration(
        cost_element_id=cost_element.cost_element_id,
        registration_date=date(2024, 6, 10),
        amount=Decimal("30000.00"),
        cost_category="labor",
        invoice_number="INV-001",
    )
    db.add(cost_reg)
    db.commit()

    # Create earned value entry
    ev_entry = EarnedValueEntry(
        cost_element_id=cost_element.cost_element_id,
        completion_date=date(2024, 6, 10),
        percent_complete=Decimal("40.00"),
        earned_value=Decimal("40000.00"),
    )
    db.add(ev_entry)
    db.commit()

    # Create schedule
    schedule = CostElementSchedule(
        cost_element_id=cost_element.cost_element_id,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        progression_type="linear",
        registration_date=date(2024, 1, 1),
    )
    db.add(schedule)
    db.commit()

    # Create baseline
    baseline_data = {
        "baseline_type": "schedule",
        "baseline_date": "2024-06-15",
        "milestone_type": "kickoff",
        "description": "Test baseline",
    }
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/",
        headers=superuser_token_headers,
        json=baseline_data,
    )
    assert response.status_code == 200
    baseline = response.json()

    # Get WBE snapshot
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline['baseline_id']}/wbe-snapshots/{wbe.wbe_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    wbe_snapshot = response.json()

    # Verify metrics
    assert wbe_snapshot["budget_bac"] == "100000.00"
    assert wbe_snapshot["actual_cost"] == "30000.00"
    assert wbe_snapshot["earned_value"] == "40000.00"
    # Planned value should be calculated based on schedule at baseline_date
    assert wbe_snapshot["planned_value"] is not None

    # Get project snapshot
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline['baseline_id']}/project-snapshot",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    project_snapshot = response.json()

    # Verify project metrics match WBE metrics (since only one WBE)
    assert project_snapshot["budget_bac"] == wbe_snapshot["budget_bac"]
    assert project_snapshot["actual_cost"] == wbe_snapshot["actual_cost"]
    assert project_snapshot["earned_value"] == wbe_snapshot["earned_value"]


def test_baseline_snapshot_empty_wbe(
    db: Session, client: TestClient, superuser_token_headers: dict
) -> None:
    """Test baseline snapshot with WBE that has no cost elements."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project = create_random_project(db, user.id)

    # Create WBE with no cost elements
    wbe = create_random_wbe(db, project.project_id)

    # Create a baseline
    baseline_data = {
        "baseline_type": "schedule",
        "baseline_date": "2024-06-15",
        "milestone_type": "kickoff",
        "description": "Test baseline",
    }
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/",
        headers=superuser_token_headers,
        json=baseline_data,
    )
    assert response.status_code == 200
    baseline = response.json()

    # Get WBE snapshot (should exist with zero metrics)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline['baseline_id']}/wbe-snapshots/{wbe.wbe_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["planned_value"] == "0.00"
    assert snapshot["earned_value"] == "0.00"
    assert snapshot["actual_cost"] == "0.00"
    assert snapshot["budget_bac"] == "0.00"


def test_baseline_snapshot_empty_project(
    db: Session, client: TestClient, superuser_token_headers: dict
) -> None:
    """Test baseline snapshot with project that has no WBEs."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project with no WBEs
    project = create_random_project(db, user.id)

    # Create a baseline
    baseline_data = {
        "baseline_type": "schedule",
        "baseline_date": "2024-06-15",
        "milestone_type": "kickoff",
        "description": "Test baseline",
    }
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/",
        headers=superuser_token_headers,
        json=baseline_data,
    )
    assert response.status_code == 200
    baseline = response.json()

    # Get project snapshot (should exist with zero metrics)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline['baseline_id']}/project-snapshot",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["planned_value"] == "0.00"
    assert snapshot["earned_value"] == "0.00"
    assert snapshot["actual_cost"] == "0.00"
    assert snapshot["budget_bac"] == "0.00"


def test_baseline_snapshot_404_errors(
    db: Session, client: TestClient, superuser_token_headers: dict
) -> None:
    """Test 404 errors for snapshot endpoints."""
    # Create a user
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)

    # Create a project
    project = create_random_project(db, user.id)

    fake_baseline_id = str(uuid.uuid4())
    fake_wbe_id = str(uuid.uuid4())

    # Test 404 for non-existent baseline
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{fake_baseline_id}/wbe-snapshots",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404

    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{fake_baseline_id}/project-snapshot",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404

    # Create a baseline first
    baseline_data = {
        "baseline_type": "schedule",
        "baseline_date": "2024-06-15",
        "milestone_type": "kickoff",
        "description": "Test baseline",
    }
    response = client.post(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/",
        headers=superuser_token_headers,
        json=baseline_data,
    )
    assert response.status_code == 200
    baseline = response.json()

    # Test 404 for non-existent WBE snapshot
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/baseline-logs/{baseline['baseline_id']}/wbe-snapshots/{fake_wbe_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
