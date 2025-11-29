"""Tests for Branch locking API routes."""

import uuid
from datetime import date

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import (
    BranchLock,
    ChangeOrder,
    Project,
    User,
    UserCreate,
    UserRole,
)
from app.services.branch_service import BranchService
from tests.utils.user import user_authentication_headers


def _create_pm_user(session: Session) -> User:
    """Helper to create a project manager user."""
    from app import crud

    email = f"pm_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password, role=UserRole.project_manager)
    return crud.create_user(session=session, user_create=user_in)


def _create_admin_user(session: Session) -> User:
    """Helper to create an admin user."""
    from app import crud

    email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password, role=UserRole.admin)
    return crud.create_user(session=session, user_create=user_in)


def _create_controller_user(session: Session) -> User:
    """Helper to create a controller user (not project manager or admin)."""
    from app import crud

    email = f"controller_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password, role=UserRole.controller)
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


def _create_change_order(session: Session, project: Project, user: User) -> ChangeOrder:
    """Helper to create a change order with branch."""
    from app.models import ChangeOrderCreate

    co_in = ChangeOrderCreate(
        project_id=project.project_id,
        created_by_id=user.id,
        change_order_number="CO-TEST-001",
        title="Test Change Order",
        description="Test description",
        requesting_party="Customer",
        effective_date=date(2024, 6, 1),
        workflow_status="design",
    )
    change_order = ChangeOrder.model_validate(co_in)
    session.add(change_order)
    session.commit()
    session.refresh(change_order)

    # Create branch for change order
    branch = BranchService.create_branch(
        session, change_order_id=change_order.change_order_id
    )
    change_order.branch = branch
    session.add(change_order)
    session.commit()
    session.refresh(change_order)

    return change_order


def test_lock_branch_as_project_manager(client: TestClient, db: Session) -> None:
    """Test that project manager can lock a branch."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = change_order.branch

    # Login
    headers = user_authentication_headers(
        client=client, email=pm_user.email, password="testpassword123"
    )

    # Lock branch
    response = client.post(
        f"/api/v1/projects/{project.project_id}/branches/{branch}/lock",
        json={"reason": "Testing lock"},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["lock_id"] is not None
    assert data["branch"] == branch
    assert data["locked_by_id"] == str(pm_user.id)
    assert data["reason"] == "Testing lock"

    # Verify lock exists in database
    lock = db.exec(
        select(BranchLock)
        .where(BranchLock.project_id == project.project_id)
        .where(BranchLock.branch == branch)
    ).first()

    assert lock is not None
    assert lock.locked_by_id == pm_user.id
    assert lock.reason == "Testing lock"


def test_lock_branch_as_admin(client: TestClient, db: Session) -> None:
    """Test that admin can lock a branch."""
    pm_user = _create_pm_user(db)
    admin_user = _create_admin_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = change_order.branch

    # Login as admin
    headers = user_authentication_headers(
        client=client, email=admin_user.email, password="testpassword123"
    )

    # Lock branch
    response = client.post(
        f"/api/v1/projects/{project.project_id}/branches/{branch}/lock",
        json={"reason": "Admin lock"},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["lock_id"] is not None
    assert data["locked_by_id"] == str(admin_user.id)


def test_lock_branch_requires_permission(client: TestClient, db: Session) -> None:
    """Test that controller (non-PM/admin) cannot lock a branch."""
    pm_user = _create_pm_user(db)
    controller_user = _create_controller_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = change_order.branch

    # Login as controller
    headers = user_authentication_headers(
        client=client,
        email=controller_user.email,
        password="testpassword123",
    )

    # Try to lock branch
    response = client.post(
        f"/api/v1/projects/{project.project_id}/branches/{branch}/lock",
        json={"reason": "Should fail"},
        headers=headers,
    )

    assert response.status_code == 403
    assert "privileges" in response.json()["detail"].lower()


def test_lock_branch_cannot_lock_main(client: TestClient, db: Session) -> None:
    """Test that main branch cannot be locked."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)

    # Login
    headers = user_authentication_headers(
        client=client, email=pm_user.email, password="testpassword123"
    )

    # Try to lock main branch
    response = client.post(
        f"/api/v1/projects/{project.project_id}/branches/main/lock",
        json={"reason": "Should fail"},
        headers=headers,
    )

    assert response.status_code == 400
    assert "main branch" in response.json()["detail"].lower()


def test_lock_branch_already_locked(client: TestClient, db: Session) -> None:
    """Test that already locked branch cannot be locked again."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = change_order.branch

    # Login
    headers = user_authentication_headers(
        client=client, email=pm_user.email, password="testpassword123"
    )

    # Lock branch first time
    response = client.post(
        f"/api/v1/projects/{project.project_id}/branches/{branch}/lock",
        json={"reason": "First lock"},
        headers=headers,
    )
    assert response.status_code == 200

    # Try to lock again
    response = client.post(
        f"/api/v1/projects/{project.project_id}/branches/{branch}/lock",
        json={"reason": "Second lock"},
        headers=headers,
    )

    assert response.status_code == 400
    assert "already locked" in response.json()["detail"].lower()


def test_lock_branch_without_reason(client: TestClient, db: Session) -> None:
    """Test that branch can be locked without reason."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = change_order.branch

    # Login
    headers = user_authentication_headers(
        client=client, email=pm_user.email, password="testpassword123"
    )

    # Lock branch without reason
    response = client.post(
        f"/api/v1/projects/{project.project_id}/branches/{branch}/lock",
        json={},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reason"] is None


def test_unlock_branch(client: TestClient, db: Session) -> None:
    """Test that branch can be unlocked."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = change_order.branch

    # Login
    headers = user_authentication_headers(
        client=client, email=pm_user.email, password="testpassword123"
    )

    # Lock branch first
    response = client.post(
        f"/api/v1/projects/{project.project_id}/branches/{branch}/lock",
        json={"reason": "Test lock"},
        headers=headers,
    )
    assert response.status_code == 200

    # Unlock branch
    response = client.delete(
        f"/api/v1/projects/{project.project_id}/branches/{branch}/lock",
        headers=headers,
    )

    assert response.status_code == 200
    assert "unlocked successfully" in response.json()["message"].lower()

    # Verify lock is removed
    lock = db.exec(
        select(BranchLock)
        .where(BranchLock.project_id == project.project_id)
        .where(BranchLock.branch == branch)
    ).first()

    assert lock is None


def test_unlock_branch_not_locked(client: TestClient, db: Session) -> None:
    """Test that unlocking a non-locked branch returns 404."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = change_order.branch

    # Login
    headers = user_authentication_headers(
        client=client, email=pm_user.email, password="testpassword123"
    )

    # Try to unlock non-locked branch
    response = client.delete(
        f"/api/v1/projects/{project.project_id}/branches/{branch}/lock",
        headers=headers,
    )

    assert response.status_code == 404
    assert "not locked" in response.json()["detail"].lower()


def test_get_branch_lock_status(client: TestClient, db: Session) -> None:
    """Test getting lock status for a branch."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = change_order.branch

    # Login
    headers = user_authentication_headers(
        client=client, email=pm_user.email, password="testpassword123"
    )

    # Lock branch
    response = client.post(
        f"/api/v1/projects/{project.project_id}/branches/{branch}/lock",
        json={"reason": "Test"},
        headers=headers,
    )
    assert response.status_code == 200

    # Get lock status
    response = client.get(
        f"/api/v1/projects/{project.project_id}/branches/{branch}/lock",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["branch"] == branch
    assert data["locked_by_id"] == str(pm_user.id)
    assert data["reason"] == "Test"


def test_get_branch_lock_status_not_locked(client: TestClient, db: Session) -> None:
    """Test getting lock status for a non-locked branch returns None."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order = _create_change_order(db, project, pm_user)
    branch = change_order.branch

    # Login
    headers = user_authentication_headers(
        client=client, email=pm_user.email, password="testpassword123"
    )

    # Get lock status for non-locked branch
    response = client.get(
        f"/api/v1/projects/{project.project_id}/branches/{branch}/lock",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() is None


def test_list_branch_locks(client: TestClient, db: Session) -> None:
    """Test listing all branch locks for a project."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)
    change_order1 = _create_change_order(db, project, pm_user)
    branch1 = change_order1.branch

    # Create second change order
    from app.models import ChangeOrderBase

    co_data2 = ChangeOrderBase(
        project_id=project.project_id,
        change_order_number="CO-TEST-002",
        title="Test Change Order 2",
        description="Test description 2",
        requesting_party="Customer",
        effective_date=date(2024, 6, 2),
        workflow_status="design",
    )
    change_order2 = ChangeOrder.model_validate(co_data2)
    change_order2.created_by_id = pm_user.id
    db.add(change_order2)
    db.commit()
    db.refresh(change_order2)
    branch2 = BranchService.create_branch(
        db, change_order_id=change_order2.change_order_id
    )
    change_order2.branch = branch2
    db.add(change_order2)
    db.commit()

    # Login
    headers = user_authentication_headers(
        client=client, email=pm_user.email, password="testpassword123"
    )

    # Lock first branch
    response = client.post(
        f"/api/v1/projects/{project.project_id}/branches/{branch1}/lock",
        json={"reason": "Lock 1"},
        headers=headers,
    )
    assert response.status_code == 200

    # Lock second branch
    response = client.post(
        f"/api/v1/projects/{project.project_id}/branches/{branch2}/lock",
        json={"reason": "Lock 2"},
        headers=headers,
    )
    assert response.status_code == 200

    # List all locks
    response = client.get(
        f"/api/v1/projects/{project.project_id}/branches/locks",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "locks" in data
    assert branch1 in data["locks"]
    assert branch2 in data["locks"]
    assert data["locks"][branch1]["reason"] == "Lock 1"
    assert data["locks"][branch2]["reason"] == "Lock 2"
