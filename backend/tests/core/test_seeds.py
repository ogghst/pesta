"""Tests for seed functions."""
from unittest.mock import patch

from sqlmodel import Session, delete, select

from app.core.seeds import _seed_cost_element_types, _seed_departments
from app.models import CostElementType, Department


def test_seed_departments_creates_records(db: Session) -> None:
    """Test that _seed_departments creates departments from JSON file."""
    # Run seed function (will use actual JSON file)
    _seed_departments(db)

    # Verify at least one department from seed file was created
    department = db.exec(
        select(Department).where(Department.department_code == "MECH")
    ).first()

    assert department is not None
    assert department.department_code == "MECH"
    assert department.department_name == "Mechanical Engineering"
    assert department.is_active is True


def test_seed_departments_idempotent(db: Session) -> None:
    """Test that _seed_departments doesn't create duplicates on re-run."""
    # Run seed function first time
    _seed_departments(db)
    count_first = len(db.exec(select(Department)).all())

    # Run seed function second time
    _seed_departments(db)
    count_second = len(db.exec(select(Department)).all())

    assert count_second == count_first, "Should not create duplicate departments"


def test_seed_departments_missing_file(db: Session) -> None:
    """Test that _seed_departments handles missing file gracefully."""
    # Count before (may have departments from other tests)
    count_before = len(db.exec(select(Department)).all())

    # Mock Path so the seed file appears to not exist
    with patch("app.core.seeds.Path") as mock_path:
        # Set up the mock chain: Path(__file__).parent / "departments_seed.json"
        mock_file_path_instance = mock_path.return_value
        mock_parent = mock_file_path_instance.parent
        mock_seed_file = mock_parent.__truediv__.return_value
        mock_seed_file.exists.return_value = False

        # Should not raise exception
        _seed_departments(db)

    # Verify no new departments were created
    count_after = len(db.exec(select(Department)).all())
    assert (
        count_after == count_before
    ), "Should not create departments when file doesn't exist"


def test_seed_order_departments_first(db: Session) -> None:
    """Integration test: departments must be seeded before cost element types."""
    from app.core.db import init_db

    # Clear existing data
    statement = delete(CostElementType)
    db.execute(statement)
    statement = delete(Department)
    db.execute(statement)
    db.commit()

    # Run init_db which should seed departments first
    init_db(db)

    # Verify departments were created
    departments = db.exec(select(Department)).all()
    assert len(departments) > 0, "Departments should be seeded"

    # Verify cost element types were created and can reference departments
    cost_element_types = db.exec(select(CostElementType)).all()
    assert len(cost_element_types) > 0, "Cost element types should be seeded"

    # Verify at least one cost element type has a department reference
    cet_with_dept = next(
        (cet for cet in cost_element_types if cet.department_id is not None), None
    )
    assert cet_with_dept is not None, "Cost element types should reference departments"

    # Refresh to load relationship
    db.refresh(cet_with_dept)
    assert (
        cet_with_dept.department is not None
    ), "Department relationship should be loaded"


def test_seed_cost_element_types_still_works(db: Session) -> None:
    """Regression test: verify cost element types seed function still works after refactor."""
    # Clear existing data
    statement = delete(CostElementType)
    db.execute(statement)
    statement = delete(Department)
    db.execute(statement)
    db.commit()

    # Seed departments first (dependency)
    _seed_departments(db)

    # Seed cost element types
    _seed_cost_element_types(db)

    # Verify cost element types were created
    cost_element_types = db.exec(select(CostElementType)).all()
    assert len(cost_element_types) > 0, "Cost element types should be seeded"

    # Verify they can reference departments
    cet_with_dept = next(
        (cet for cet in cost_element_types if cet.department_id is not None), None
    )
    assert (
        cet_with_dept is not None
    ), "Cost element types should have department references"
