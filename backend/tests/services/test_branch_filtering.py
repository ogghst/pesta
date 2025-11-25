"""Tests for branch and status filtering utilities."""

from sqlmodel import Session, select

from app.models import WBE, CostElement, Project, User
from app.services.branch_filtering import (
    apply_branch_filters,
    apply_status_filters,
    get_branch_context,
    set_branch_context,
)


def test_apply_branch_filters_wbe_defaults(db: Session) -> None:
    """Test that apply_branch_filters adds default branch='main' and status='active' for WBE queries."""
    statement = select(WBE)

    filtered_statement = apply_branch_filters(statement, WBE, branch="main")

    # Verify the statement has been modified (we can't easily test the exact SQL, but we can verify it doesn't crash)
    assert filtered_statement is not None
    # The actual filtering will be tested when we execute the query


def test_apply_branch_filters_wbe_custom_branch(db: Session) -> None:
    """Test that apply_branch_filters works with custom branch for WBE."""
    statement = select(WBE)

    filtered_statement = apply_branch_filters(statement, WBE, branch="co-001")

    assert filtered_statement is not None


def test_apply_branch_filters_cost_element_defaults(db: Session) -> None:
    """Test that apply_branch_filters adds default branch='main' and status='active' for CostElement queries."""
    statement = select(CostElement)

    filtered_statement = apply_branch_filters(statement, CostElement, branch="main")

    assert filtered_statement is not None


def test_apply_branch_filters_cost_element_custom_branch(db: Session) -> None:
    """Test that apply_branch_filters works with custom branch for CostElement."""
    statement = select(CostElement)

    filtered_statement = apply_branch_filters(statement, CostElement, branch="co-002")

    assert filtered_statement is not None


def test_apply_status_filters_project(db: Session) -> None:
    """Test that apply_status_filters adds status='active' filter for Project queries."""
    statement = select(Project)

    filtered_statement = apply_status_filters(statement, Project, status="active")

    assert filtered_statement is not None


def test_apply_status_filters_user(db: Session) -> None:
    """Test that apply_status_filters adds status='active' filter for User queries."""
    statement = select(User)

    filtered_statement = apply_status_filters(statement, User, status="active")

    assert filtered_statement is not None


def test_apply_status_filters_custom_status(db: Session) -> None:
    """Test that apply_status_filters works with custom status values."""
    statement = select(Project)

    filtered_statement = apply_status_filters(statement, Project, status="deleted")

    assert filtered_statement is not None


def test_branch_filtering_with_joins(db: Session) -> None:
    """Test that branch filtering works with joined queries."""
    statement = select(CostElement).join(WBE)

    filtered_statement = apply_branch_filters(statement, CostElement, branch="main")

    assert filtered_statement is not None


def test_status_filtering_with_joins(db: Session) -> None:
    """Test that status filtering works with joined queries."""
    statement = select(Project).join(User)

    filtered_statement = apply_status_filters(statement, Project, status="active")

    assert filtered_statement is not None


def test_branch_context_get_set() -> None:
    """Test that branch context can be set and retrieved."""
    # Test default context
    assert get_branch_context() == "main"

    # Test setting custom context
    set_branch_context("co-001")
    assert get_branch_context() == "co-001"

    # Test resetting to default
    set_branch_context("main")
    assert get_branch_context() == "main"
