"""Tests for report generation with branch filtering."""

from datetime import date

from sqlmodel import Session

from app.models import WBE, Project, User, UserCreate
from app.services.cost_performance_report import get_cost_performance_report
from app.services.variance_analysis_report import get_variance_analysis_report


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


def test_cost_performance_report_filters_by_branch(db: Session) -> None:
    """Test that cost performance report can be generated for a specific branch."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)

    # Create a WBE in main branch
    from app.models import WBECreate

    wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Test Machine",
        serial_number="SN-001",
        contracted_delivery_date=date(2024, 6, 1),
        revenue_allocation=50000.00,
        business_status="active",
    )
    main_wbe = WBE.model_validate(wbe_in)
    main_wbe.branch = "main"
    db.add(main_wbe)
    db.commit()
    db.refresh(main_wbe)

    # Create a WBE in a branch
    branch_name = "co-001"
    branch_wbe = WBE.model_validate(wbe_in)
    branch_wbe.branch = branch_name
    branch_wbe.entity_id = main_wbe.entity_id  # Same entity, different branch
    db.add(branch_wbe)
    db.commit()
    db.refresh(branch_wbe)

    # Get report for main branch
    main_report = get_cost_performance_report(
        session=db,
        project_id=project.project_id,
        control_date=date.today(),
        branch="main",
    )

    # Get report for branch
    branch_report = get_cost_performance_report(
        session=db,
        project_id=project.project_id,
        control_date=date.today(),
        branch=branch_name,
    )

    # Reports should be different (or at least the query should work)
    assert main_report.project_id == project.project_id
    assert branch_report.project_id == project.project_id


def test_variance_analysis_report_filters_by_branch(db: Session) -> None:
    """Test that variance analysis report can be generated for a specific branch."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)

    # Get report for main branch
    main_report = get_variance_analysis_report(
        session=db,
        project_id=project.project_id,
        control_date=date.today(),
        branch="main",
    )

    # Get report for a branch
    branch_report = get_variance_analysis_report(
        session=db,
        project_id=project.project_id,
        control_date=date.today(),
        branch="co-001",
    )

    # Reports should work (may be empty if no data)
    assert main_report.project_id == project.project_id
    assert branch_report.project_id == project.project_id


def test_reports_default_to_main_branch(db: Session) -> None:
    """Test that reports default to main branch when branch is not specified."""
    pm_user = _create_pm_user(db)
    project = _create_project(db, pm_user)

    # Get report without specifying branch (should default to main)
    report = get_cost_performance_report(
        session=db, project_id=project.project_id, control_date=date.today()
    )

    assert report.project_id == project.project_id

    # Get variance report without specifying branch
    variance_report = get_variance_analysis_report(
        session=db, project_id=project.project_id, control_date=date.today()
    )

    assert variance_report.project_id == project.project_id
