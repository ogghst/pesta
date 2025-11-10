"""Tests for planned value API endpoints."""
import uuid
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import (
    WBE,
    CostElement,
    CostElementCreate,
    CostElementType,
    CostElementTypeCreate,
    Project,
    ProjectCreate,
    UserCreate,
    WBECreate,
)
from tests.utils.cost_element_schedule import create_schedule_for_cost_element
from tests.utils.cost_element_type import create_random_cost_element_type


def _create_project_with_manager(db: Session) -> tuple[Project, uuid.UUID]:
    email = f"pm_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    pm_user = crud.create_user(session=db, user_create=user_in)

    project_in = ProjectCreate(
        project_name="PV Test Project",
        customer_name="PV Customer",
        contract_value=Decimal("250000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=pm_user.id,
        status="active",
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project, pm_user.id


def _create_cost_element_type(db: Session) -> CostElementType:
    cet_in = CostElementTypeCreate(
        type_code=f"pv_type_{uuid.uuid4().hex[:8]}",
        type_name="PV Engineering",
        category_type="engineering_mechanical",
        display_order=1,
        is_active=True,
    )
    cet = CostElementType.model_validate(cet_in)
    db.add(cet)
    db.commit()
    db.refresh(cet)
    return cet


def _create_wbe(db: Session, project_id: uuid.UUID, revenue: Decimal) -> WBE:
    wbe_in = WBECreate(
        project_id=project_id,
        machine_type="PV Machine",
        revenue_allocation=revenue,
        status="designing",
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)
    return wbe


def _create_cost_element(
    db: Session,
    wbe_id: uuid.UUID,
    cet: CostElementType,
    *,
    department_code: str,
    department_name: str,
    budget_bac: Decimal,
    revenue_plan: Decimal,
) -> CostElement:
    ce_in = CostElementCreate(
        wbe_id=wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code=department_code,
        department_name=department_name,
        budget_bac=budget_bac,
        revenue_plan=revenue_plan,
        status="active",
    )
    ce = CostElement.model_validate(ce_in)
    db.add(ce)
    db.commit()
    db.refresh(ce)
    return ce


def test_get_planned_value_for_cost_element(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    project, created_by_id = _create_project_with_manager(db)
    cet = _create_cost_element_type(db)
    wbe = _create_wbe(db, project.project_id, Decimal("80000.00"))

    cost_element = _create_cost_element(
        db,
        wbe.wbe_id,
        cet,
        department_code="ENG",
        department_name="Engineering",
        budget_bac=Decimal("100000.00"),
        revenue_plan=Decimal("120000.00"),
    )

    create_schedule_for_cost_element(
        db,
        cost_element.cost_element_id,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 1),
        progression_type="linear",
        created_by_id=created_by_id,
    )

    control_date = date(2024, 2, 1)
    response = client.get(
        (
            f"{settings.API_V1_STR}/projects/{project.project_id}"
            f"/planned-value/cost-elements/{cost_element.cost_element_id}"
        ),
        headers=superuser_token_headers,
        params={"control_date": control_date.isoformat()},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["level"] == "cost-element"
    assert data["cost_element_id"] == str(cost_element.cost_element_id)
    assert data["control_date"] == control_date.isoformat()
    assert Decimal(data["planned_value"]) == Decimal("50000.00")
    assert Decimal(data["percent_complete"]) == Decimal("0.50")
    assert Decimal(data["budget_bac"]) == Decimal("100000.00")


def test_get_planned_value_for_wbe(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    project, created_by_id = _create_project_with_manager(db)
    cet = _create_cost_element_type(db)
    wbe = _create_wbe(db, project.project_id, Decimal("150000.00"))

    ce1 = _create_cost_element(
        db,
        wbe.wbe_id,
        cet,
        department_code="ENG1",
        department_name="Engineering 1",
        budget_bac=Decimal("60000.00"),
        revenue_plan=Decimal("70000.00"),
    )
    ce2 = _create_cost_element(
        db,
        wbe.wbe_id,
        cet,
        department_code="ENG2",
        department_name="Engineering 2",
        budget_bac=Decimal("40000.00"),
        revenue_plan=Decimal("50000.00"),
    )

    create_schedule_for_cost_element(
        db,
        ce1.cost_element_id,
        start_date=date(2024, 4, 1),
        end_date=date(2024, 7, 1),
        progression_type="linear",
        created_by_id=created_by_id,
    )
    create_schedule_for_cost_element(
        db,
        ce2.cost_element_id,
        start_date=date(2024, 4, 1),
        end_date=date(2024, 7, 1),
        progression_type="logarithmic",
        created_by_id=created_by_id,
    )

    control_date = date(2024, 5, 16)
    response = client.get(
        (
            f"{settings.API_V1_STR}/projects/{project.project_id}"
            f"/planned-value/wbes/{wbe.wbe_id}"
        ),
        headers=superuser_token_headers,
        params={"control_date": control_date.isoformat()},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["level"] == "wbe"
    assert data["wbe_id"] == str(wbe.wbe_id)
    assert data["control_date"] == control_date.isoformat()

    # Expected PV combines linear 50% of 60k plus logarithmic percent (should be >0 and <1).
    assert Decimal(data["planned_value"]) > Decimal("30000.00")
    assert Decimal(data["planned_value"]) < Decimal("60000.00")
    assert Decimal(data["budget_bac"]) == Decimal("100000.00")


def test_get_planned_value_for_project(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    project, created_by_id = _create_project_with_manager(db)
    cet = _create_cost_element_type(db)

    wbe1 = _create_wbe(db, project.project_id, Decimal("80000.00"))
    wbe2 = _create_wbe(db, project.project_id, Decimal("90000.00"))

    ce1 = _create_cost_element(
        db,
        wbe1.wbe_id,
        cet,
        department_code="ENG1",
        department_name="Engineering 1",
        budget_bac=Decimal("30000.00"),
        revenue_plan=Decimal("35000.00"),
    )
    ce2 = _create_cost_element(
        db,
        wbe2.wbe_id,
        cet,
        department_code="ENG2",
        department_name="Engineering 2",
        budget_bac=Decimal("50000.00"),
        revenue_plan=Decimal("55000.00"),
    )

    create_schedule_for_cost_element(
        db,
        ce1.cost_element_id,
        start_date=date(2024, 6, 1),
        end_date=date(2024, 9, 1),
        progression_type="gaussian",
        created_by_id=created_by_id,
    )
    create_schedule_for_cost_element(
        db,
        ce2.cost_element_id,
        start_date=date(2024, 7, 1),
        end_date=date(2024, 10, 1),
        progression_type="linear",
        created_by_id=created_by_id,
    )

    control_date = date(2024, 8, 1)
    response = client.get(
        f"{settings.API_V1_STR}/projects/{project.project_id}/planned-value",
        headers=superuser_token_headers,
        params={"control_date": control_date.isoformat()},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["level"] == "project"
    assert data["project_id"] == str(project.project_id)
    assert data["control_date"] == control_date.isoformat()
    assert Decimal(data["budget_bac"]) == Decimal("80000.00")
    assert Decimal(data["planned_value"]) > Decimal("0.00")
    assert Decimal(data["planned_value"]) < Decimal("80000.00")


def test_planned_value_requires_control_date(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    project, created_by_id = _create_project_with_manager(db)
    cet = _create_cost_element_type(db)
    wbe = _create_wbe(db, project.project_id, Decimal("50000.00"))
    cost_element = _create_cost_element(
        db,
        wbe.wbe_id,
        cet,
        department_code="ENG",
        department_name="Engineering",
        budget_bac=Decimal("30000.00"),
        revenue_plan=Decimal("35000.00"),
    )
    create_schedule_for_cost_element(
        db,
        cost_element.cost_element_id,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 1),
        progression_type="linear",
        created_by_id=created_by_id,
    )

    response = client.get(
        (
            f"{settings.API_V1_STR}/projects/{project.project_id}"
            f"/planned-value/cost-elements/{cost_element.cost_element_id}"
        ),
        headers=superuser_token_headers,
    )

    assert response.status_code == 422


def quantize(value: Decimal) -> Decimal:
    """Helper to quantize planned value to two decimal places with HALF_UP rounding."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _create_project_with_manager(db: Session) -> tuple[Project, uuid.UUID]:
    """Create a project with a project manager user."""
    email = f"pm_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    pm_user = crud.create_user(session=db, user_create=user_in)

    project_in = ProjectCreate(
        project_name="PV Project",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date(2024, 1, 1),
        planned_completion_date=date(2024, 12, 31),
        project_manager_id=pm_user.id,
        status="active",
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project, pm_user.id


def _create_wbe(db: Session, project: Project) -> WBE:
    wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Machine A",
        revenue_allocation=Decimal("50000.00"),
        status="designing",
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)
    return wbe


def test_get_cost_element_planned_value_linear(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Linear schedule should yield proportional planned value on control date."""
    project, created_by_id = _create_project_with_manager(db)
    wbe = _create_wbe(db, project)
    cost_element_type = create_random_cost_element_type(db)

    ce_in = CostElementCreate(
        wbe_id=wbe.wbe_id,
        cost_element_type_id=cost_element_type.cost_element_type_id,
        department_code="ENG",
        department_name="Engineering",
        budget_bac=Decimal("100000.00"),
        revenue_plan=Decimal("120000.00"),
        status="active",
    )
    cost_element = CostElement.model_validate(ce_in)
    db.add(cost_element)
    db.commit()
    db.refresh(cost_element)

    start = date(2024, 1, 1)
    end = date(2024, 1, 31)
    control_date = start + timedelta(days=15)

    create_schedule_for_cost_element(
        db,
        cost_element_id=cost_element.cost_element_id,
        start_date=start,
        end_date=end,
        progression_type="linear",
        created_by_id=created_by_id,
    )

    response = client.get(
        f"{settings.API_V1_STR}/planned-value/cost-element/{cost_element.cost_element_id}",
        headers=superuser_token_headers,
        params={"control_date": control_date.isoformat()},
    )

    assert response.status_code == 200
    content = response.json()

    assert content["level"] == "cost-element"
    assert content["cost_element_id"] == str(cost_element.cost_element_id)
    assert content["control_date"] == control_date.isoformat()
    assert Decimal(content["budget_bac"]) == Decimal("100000.00")
    assert Decimal(content["planned_value"]) == Decimal("50000.00")
    assert Decimal(content["percent_complete"]) == Decimal("0.50")


def test_get_wbe_planned_value_aggregates_cost_elements(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """WBE planned value should aggregate across cost elements weighted by BAC."""
    project, created_by_id = _create_project_with_manager(db)
    wbe = _create_wbe(db, project)
    cost_element_type = create_random_cost_element_type(db)

    ce1_in = CostElementCreate(
        wbe_id=wbe.wbe_id,
        cost_element_type_id=cost_element_type.cost_element_type_id,
        department_code="ENG",
        department_name="Engineering",
        budget_bac=Decimal("80000.00"),
        revenue_plan=Decimal("90000.00"),
        status="active",
    )
    ce1 = CostElement.model_validate(ce1_in)
    db.add(ce1)
    db.commit()
    db.refresh(ce1)

    ce2_in = CostElementCreate(
        wbe_id=wbe.wbe_id,
        cost_element_type_id=cost_element_type.cost_element_type_id,
        department_code="PROC",
        department_name="Procurement",
        budget_bac=Decimal("40000.00"),
        revenue_plan=Decimal("45000.00"),
        status="active",
    )
    ce2 = CostElement.model_validate(ce2_in)
    db.add(ce2)
    db.commit()
    db.refresh(ce2)

    control_date = date(2024, 2, 1)

    # First cost element spans one month
    create_schedule_for_cost_element(
        db,
        cost_element_id=ce1.cost_element_id,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        progression_type="linear",
        created_by_id=created_by_id,
    )

    # Second cost element spans two months (less complete on same control date)
    create_schedule_for_cost_element(
        db,
        cost_element_id=ce2.cost_element_id,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 1),
        progression_type="linear",
        created_by_id=created_by_id,
    )

    total_days_ce2 = (date(2024, 3, 1) - date(2024, 1, 1)).days
    days_elapsed_ce2 = (control_date - date(2024, 1, 1)).days

    pv_ce1 = quantize(Decimal("80000.00"))  # completed by Feb 1
    percent_ce2 = min(
        Decimal(days_elapsed_ce2) / Decimal(total_days_ce2), Decimal("1.0")
    )
    pv_ce2 = quantize(Decimal("40000.00") * percent_ce2)
    expected_total = quantize(pv_ce1 + pv_ce2)
    expected_percent = quantize(
        expected_total / (Decimal("80000.00") + Decimal("40000.00"))
    )

    response = client.get(
        f"{settings.API_V1_STR}/planned-value/wbe/{wbe.wbe_id}",
        headers=superuser_token_headers,
        params={"control_date": control_date.isoformat()},
    )

    assert response.status_code == 200
    content = response.json()

    assert content["level"] == "wbe"
    assert content["wbe_id"] == str(wbe.wbe_id)
    assert content["control_date"] == control_date.isoformat()
    assert Decimal(content["planned_value"]) == expected_total
    assert Decimal(content["budget_bac"]) == Decimal("120000.00")
    assert Decimal(content["percent_complete"]) == expected_percent


def test_get_project_planned_value_sums_wbes(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Project planned value should roll up across WBEs."""
    project, created_by_id = _create_project_with_manager(db)
    wbe1 = _create_wbe(db, project)
    wbe2 = _create_wbe(db, project)
    cost_element_type = create_random_cost_element_type(db)

    # WBE 1 cost element
    ce1_in = CostElementCreate(
        wbe_id=wbe1.wbe_id,
        cost_element_type_id=cost_element_type.cost_element_type_id,
        department_code="ENG1",
        department_name="Engineering 1",
        budget_bac=Decimal("60000.00"),
        revenue_plan=Decimal("70000.00"),
        status="active",
    )
    ce1 = CostElement.model_validate(ce1_in)
    db.add(ce1)
    db.commit()
    db.refresh(ce1)

    # WBE 2 cost element
    ce2_in = CostElementCreate(
        wbe_id=wbe2.wbe_id,
        cost_element_type_id=cost_element_type.cost_element_type_id,
        department_code="ENG2",
        department_name="Engineering 2",
        budget_bac=Decimal("50000.00"),
        revenue_plan=Decimal("60000.00"),
        status="active",
    )
    ce2 = CostElement.model_validate(ce2_in)
    db.add(ce2)
    db.commit()
    db.refresh(ce2)

    control_date = date(2024, 1, 20)

    create_schedule_for_cost_element(
        db,
        cost_element_id=ce1.cost_element_id,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 2, 1),
        progression_type="linear",
        created_by_id=created_by_id,
    )

    create_schedule_for_cost_element(
        db,
        cost_element_id=ce2.cost_element_id,
        start_date=date(2024, 1, 10),
        end_date=date(2024, 2, 20),
        progression_type="linear",
        created_by_id=created_by_id,
    )

    # Compute expected PVs
    total_days_ce1 = (date(2024, 2, 1) - date(2024, 1, 1)).days
    percent_ce1 = min(
        Decimal((control_date - date(2024, 1, 1)).days) / Decimal(total_days_ce1),
        Decimal("1.0"),
    )
    pv_ce1 = quantize(Decimal("60000.00") * percent_ce1)

    total_days_ce2 = (date(2024, 2, 20) - date(2024, 1, 10)).days
    percent_ce2 = min(
        Decimal((control_date - date(2024, 1, 10)).days) / Decimal(total_days_ce2),
        Decimal("1.0"),
    )
    pv_ce2 = quantize(Decimal("50000.00") * percent_ce2)

    total_budget = Decimal("110000.00")
    expected_total = quantize(pv_ce1 + pv_ce2)
    expected_percent = quantize(expected_total / total_budget)

    response = client.get(
        f"{settings.API_V1_STR}/planned-value/project/{project.project_id}",
        headers=superuser_token_headers,
        params={"control_date": control_date.isoformat()},
    )

    assert response.status_code == 200
    content = response.json()

    assert content["level"] == "project"
    assert content["project_id"] == str(project.project_id)
    assert content["control_date"] == control_date.isoformat()
    assert Decimal(content["planned_value"]) == expected_total
    assert Decimal(content["budget_bac"]) == total_budget
    assert Decimal(content["percent_complete"]) == expected_percent


def test_cost_element_planned_value_without_schedule_returns_zero(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Cost element without a schedule should return zero planned value."""
    project, _ = _create_project_with_manager(db)
    wbe = _create_wbe(db, project)
    cost_element_type = create_random_cost_element_type(db)

    ce_in = CostElementCreate(
        wbe_id=wbe.wbe_id,
        cost_element_type_id=cost_element_type.cost_element_type_id,
        department_code="ENG",
        department_name="Engineering",
        budget_bac=Decimal("75000.00"),
        revenue_plan=Decimal("80000.00"),
        status="active",
    )
    cost_element = CostElement.model_validate(ce_in)
    db.add(cost_element)
    db.commit()
    db.refresh(cost_element)

    control_date = date(2024, 1, 15)

    response = client.get(
        f"{settings.API_V1_STR}/planned-value/cost-element/{cost_element.cost_element_id}",
        headers=superuser_token_headers,
        params={"control_date": control_date.isoformat()},
    )

    assert response.status_code == 200
    content = response.json()

    assert Decimal(content["planned_value"]) == Decimal("0.00")
    assert Decimal(content["percent_complete"]) == Decimal("0.00")


def test_planned_value_not_found_returns_404(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Unknown identifiers should yield 404 errors."""
    control_date = date(2024, 1, 15).isoformat()

    for path in [
        f"{settings.API_V1_STR}/planned-value/cost-element/{uuid.uuid4()}",
        f"{settings.API_V1_STR}/planned-value/wbe/{uuid.uuid4()}",
        f"{settings.API_V1_STR}/planned-value/project/{uuid.uuid4()}",
    ]:
        response = client.get(
            path, headers=superuser_token_headers, params={"control_date": control_date}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
