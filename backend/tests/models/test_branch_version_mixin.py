"""Tests for BranchVersionMixin."""

import uuid

from sqlmodel import Field, Session, SQLModel

from app.models import BranchVersionMixin, VersionStatusMixin


# Test model that uses BranchVersionMixin
class TestBranchModelBase(SQLModel):
    """Base schema for test model with branch."""

    name: str = Field(max_length=100)


class TestBranchModel(TestBranchModelBase, BranchVersionMixin, table=True):
    """Test model that inherits from BranchVersionMixin."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


def test_branch_version_mixin_extends_version_status_mixin() -> None:
    """Test that BranchVersionMixin extends VersionStatusMixin."""
    assert issubclass(BranchVersionMixin, VersionStatusMixin)
    assert issubclass(BranchVersionMixin, SQLModel)


def test_branch_version_mixin_includes_all_fields() -> None:
    """Test that BranchVersionMixin includes version, status, and branch fields."""
    instance = TestBranchModel(name="Test Item")

    # Check that all fields exist with correct defaults
    assert hasattr(instance, "version")
    assert instance.version == 1

    assert hasattr(instance, "status")
    assert instance.status == "active"

    assert hasattr(instance, "branch")
    assert instance.branch == "main"


def test_branch_version_mixin_custom_values() -> None:
    """Test that BranchVersionMixin fields can be set to custom values."""
    instance = TestBranchModel(
        name="Test Item", version=3, status="deleted", branch="co-001"
    )

    assert instance.version == 3
    assert instance.status == "deleted"
    assert instance.branch == "co-001"


def test_branch_version_mixin_can_be_inherited() -> None:
    """Test that BranchVersionMixin can be inherited by a model."""
    assert issubclass(TestBranchModel, BranchVersionMixin)
    assert issubclass(TestBranchModel, VersionStatusMixin)
    assert issubclass(TestBranchModel, TestBranchModelBase)
    assert issubclass(TestBranchModel, SQLModel)


def test_branch_version_mixin_fields_accessible(_db: Session) -> None:
    """Test that BranchVersionMixin fields are accessible on model instances."""
    instance = TestBranchModel(name="Test Item")

    # Verify all fields are accessible
    assert instance.version is not None
    assert instance.status is not None
    assert instance.branch is not None

    # Verify fields can be modified
    instance.version = 2
    instance.status = "merged"
    instance.branch = "co-002"

    assert instance.version == 2
    assert instance.status == "merged"
    assert instance.branch == "co-002"
