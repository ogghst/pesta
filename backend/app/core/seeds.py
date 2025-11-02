"""Seed functions for initializing database with reference data."""
import json
from pathlib import Path

from sqlmodel import Session, select

from app.models import (
    CostElementType,
    CostElementTypeCreate,
    Department,
    DepartmentCreate,
)


def _seed_cost_element_types(session: Session) -> None:
    """Seed cost element types from JSON file if not already present."""
    # Load seed data from JSON file
    seed_file = Path(__file__).parent / "cost_element_types_seed.json"
    if not seed_file.exists():
        return  # No seed file, skip seeding

    with open(seed_file, encoding="utf-8") as f:
        seed_data = json.load(f)

    # Seed each cost element type if it doesn't already exist
    for item in seed_data:
        existing = session.exec(
            select(CostElementType).where(
                CostElementType.type_code == item["type_code"]
            )
        ).first()

        # Get department_code from item (not part of CostElementTypeCreate)
        department_code = item.get("department_code")

        if not existing:
            # Create new cost element type
            cet_data = {k: v for k, v in item.items() if k != "department_code"}
            cet_in = CostElementTypeCreate(**cet_data)
            cet = CostElementType.model_validate(cet_in)

            # Look up department by code and assign department_id
            if department_code:
                department = session.exec(
                    select(Department).where(
                        Department.department_code == department_code
                    )
                ).first()
                if department:
                    cet.department_id = department.department_id

            session.add(cet)
        elif existing and department_code and not existing.department_id:
            # Update existing cost element type if it doesn't have a department_id
            # Look up department by code and assign department_id
            department = session.exec(
                select(Department).where(Department.department_code == department_code)
            ).first()
            if department:
                existing.department_id = department.department_id
                session.add(existing)

    session.commit()


def _seed_departments(session: Session) -> None:
    """Seed departments from JSON file if not already present."""
    # Load seed data from JSON file
    seed_file = Path(__file__).parent / "departments_seed.json"
    if not seed_file.exists():
        return  # No seed file, skip seeding

    with open(seed_file, encoding="utf-8") as f:
        seed_data = json.load(f)

    # Seed each department if it doesn't already exist
    for item in seed_data:
        existing = session.exec(
            select(Department).where(
                Department.department_code == item["department_code"]
            )
        ).first()
        if not existing:
            dept_in = DepartmentCreate(**item)
            dept = Department.model_validate(dept_in)
            session.add(dept)

    session.commit()
