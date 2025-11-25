"""Tests for VersionStatusMixin."""

import uuid

from sqlmodel import Field, Session, SQLModel

from app.models import VersionStatusMixin


# Test model that uses VersionStatusMixin
class TestModelBase(SQLModel):
    """Base schema for test model."""

    name: str = Field(max_length=100)


class TestModel(TestModelBase, VersionStatusMixin, table=True):
    """Test model that inherits from VersionStatusMixin."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


def test_version_status_mixin_provides_fields() -> None:
    """Test that VersionStatusMixin provides entity_id, version, and status fields."""
    # Create instance without specifying version/status (should use defaults)
    instance = TestModel(name="Test Item")

    # Check that entity_id exists and is a UUID
    assert hasattr(instance, "entity_id")
    assert isinstance(instance.entity_id, uuid.UUID)

    # Check that version field exists and has default value
    assert hasattr(instance, "version")
    assert instance.version == 1

    # Check that status field exists and has default value
    assert hasattr(instance, "status")
    assert instance.status == "active"


def test_version_status_mixin_custom_values() -> None:
    """Test that VersionStatusMixin fields can be set to custom values."""
    instance = TestModel(
        name="Test Item", entity_id=uuid.uuid4(), version=5, status="deleted"
    )

    assert isinstance(instance.entity_id, uuid.UUID)
    assert instance.version == 5
    assert instance.status == "deleted"


def test_version_status_mixin_can_be_inherited() -> None:
    """Test that VersionStatusMixin can be inherited by a model."""
    # This test verifies that the mixin can be used in multiple inheritance
    assert issubclass(TestModel, VersionStatusMixin)
    assert issubclass(TestModel, TestModelBase)
    assert issubclass(TestModel, SQLModel)


def test_version_status_mixin_fields_accessible(db: Session) -> None:
    """Test that VersionStatusMixin fields are accessible on model instances."""
    instance = TestModel(name="Test Item")

    # Verify fields are accessible
    assert isinstance(instance.entity_id, uuid.UUID)
    assert instance.version is not None
    assert instance.status is not None

    # Verify fields can be modified
    new_entity_id = uuid.uuid4()
    instance.entity_id = new_entity_id
    instance.version = 2
    instance.status = "merged"

    assert instance.entity_id == new_entity_id
    assert instance.version == 2
    assert instance.status == "merged"
