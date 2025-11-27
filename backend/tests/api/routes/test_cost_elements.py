import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import BudgetAllocation, CostElement
from tests.utils.cost_element import create_random_cost_element
from tests.utils.cost_element_type import create_random_cost_element_type
from tests.utils.user import set_time_machine_date
from tests.utils.wbe import create_random_wbe


def _set_cost_element_created_at(db: Session, ce, target_date: date) -> None:
    ce.created_at = datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        tzinfo=timezone.utc,
    )
    db.add(ce)
    db.commit()
    db.refresh(ce)


@pytest.fixture(autouse=True)
def reset_time_machine(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Ensure each test starts with default time-machine date."""
    set_time_machine_date(client, superuser_token_headers, None)


def test_create_cost_element(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a cost element."""
    wbe = create_random_wbe(db)
    cost_element_type = create_random_cost_element_type(db)

    data = {
        "wbe_id": str(wbe.wbe_id),
        "cost_element_type_id": str(cost_element_type.cost_element_type_id),
        "department_code": "ENG",
        "department_name": "Engineering Department",
        "budget_bac": 10000.00,
        "revenue_plan": 12000.00,
        "business_status": "active",
    }
    response = client.post(
        f"{settings.API_V1_STR}/cost-elements/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["department_code"] == data["department_code"]
    assert content["department_name"] == data["department_name"]
    assert float(content["budget_bac"]) == data["budget_bac"]
    assert "cost_element_id" in content
    assert content["wbe_id"] == str(wbe.wbe_id)


def test_create_cost_element_invalid_wbe(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a cost element with invalid wbe_id."""
    cost_element_type = create_random_cost_element_type(db)

    data = {
        "wbe_id": str(uuid.uuid4()),
        "cost_element_type_id": str(cost_element_type.cost_element_type_id),
        "department_code": "ENG",
        "department_name": "Engineering",
        "budget_bac": 10000.00,
        "revenue_plan": 12000.00,
        "business_status": "active",
    }
    response = client.post(
        f"{settings.API_V1_STR}/cost-elements/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "WBE not found"


def test_create_cost_element_invalid_type(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a cost element with invalid cost_element_type_id."""
    wbe = create_random_wbe(db)

    data = {
        "wbe_id": str(wbe.wbe_id),
        "cost_element_type_id": str(uuid.uuid4()),
        "department_code": "ENG",
        "department_name": "Engineering",
        "budget_bac": 10000.00,
        "revenue_plan": 12000.00,
        "business_status": "active",
    }
    response = client.post(
        f"{settings.API_V1_STR}/cost-elements/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Cost element type not found"


def test_read_cost_element(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test reading a single cost element."""
    cost_element = create_random_cost_element(db)
    response = client.get(
        f"{settings.API_V1_STR}/cost-elements/{cost_element.cost_element_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["department_code"] == cost_element.department_code
    assert content["cost_element_id"] == str(cost_element.cost_element_id)


def test_read_cost_element_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test reading a non-existent cost element."""
    response = client.get(
        f"{settings.API_V1_STR}/cost-elements/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Cost element not found"


def test_read_cost_element_hidden_after_control_date(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Cost element created after control date should return 404."""
    cost_element = create_random_cost_element(db)
    future_date = date.today() + timedelta(days=45)
    _set_cost_element_created_at(db, cost_element, future_date)

    set_time_machine_date(client, superuser_token_headers, date.today())

    response = client.get(
        f"{settings.API_V1_STR}/cost-elements/{cost_element.cost_element_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404


def test_read_cost_elements_list_all(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test reading list of all cost elements."""
    create_random_cost_element(db)
    create_random_cost_element(db)
    response = client.get(
        f"{settings.API_V1_STR}/cost-elements/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 2
    assert "count" in content
    assert content["count"] >= 2


def test_read_cost_elements_filtered_by_wbe(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test reading cost elements filtered by wbe_id."""
    wbe = create_random_wbe(db)
    create_random_cost_element(db, wbe.wbe_id)
    create_random_cost_element(db, wbe.wbe_id)

    # Create another WBE with cost element
    other_wbe = create_random_wbe(db)
    create_random_cost_element(db, other_wbe.wbe_id)

    response = client.get(
        f"{settings.API_V1_STR}/cost-elements/?wbe_id={wbe.wbe_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) == 2
    assert content["count"] == 2
    # All results should belong to the requested WBE
    for ce in content["data"]:
        assert ce["wbe_id"] == str(wbe.wbe_id)


def test_read_cost_elements_respects_time_machine(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Cost elements created after control date should be hidden."""
    wbe = create_random_wbe(db)
    past_date = date.today() - timedelta(days=60)
    future_date = date.today() + timedelta(days=15)

    visible = create_random_cost_element(db, wbe.wbe_id)
    future = create_random_cost_element(db, wbe.wbe_id)
    _set_cost_element_created_at(db, visible, past_date)
    _set_cost_element_created_at(db, future, future_date)

    set_time_machine_date(client, superuser_token_headers, past_date)

    response = client.get(
        f"{settings.API_V1_STR}/cost-elements/?wbe_id={wbe.wbe_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    ids = {item["cost_element_id"] for item in content["data"]}
    assert str(visible.cost_element_id) in ids
    assert str(future.cost_element_id) not in ids


def test_update_cost_element(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating a cost element."""
    cost_element = create_random_cost_element(db)
    data = {
        "department_name": "Updated Department Name",
        "business_status": "completed",
    }
    response = client.put(
        f"{settings.API_V1_STR}/cost-elements/{cost_element.cost_element_id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["department_name"] == data["department_name"]
    assert content["business_status"] == data["business_status"]
    assert content["entity_id"] == str(cost_element.entity_id)


def test_update_cost_element_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test updating a non-existent cost element."""
    data = {"department_name": "Updated Department Name"}
    response = client.put(
        f"{settings.API_V1_STR}/cost-elements/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Cost element not found"


def test_delete_cost_element(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test deleting a cost element."""
    cost_element = create_random_cost_element(db)
    response = client.delete(
        f"{settings.API_V1_STR}/cost-elements/{cost_element.cost_element_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Cost element deleted successfully"


def test_delete_cost_element_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test deleting a non-existent cost element."""
    response = client.delete(
        f"{settings.API_V1_STR}/cost-elements/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Cost element not found"


def test_create_cost_element_exceeds_wbe_revenue_allocation(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a cost element with revenue_plan that exceeds WBE revenue_allocation."""
    from decimal import Decimal

    from app.models import WBE, WBECreate
    from tests.utils.project import create_random_project

    # Create WBE with specific revenue_allocation
    project = create_random_project(db)
    wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Test Machine",
        revenue_allocation=Decimal("10000.00"),
        status="designing",
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    cost_element_type = create_random_cost_element_type(db)

    data = {
        "wbe_id": str(wbe.wbe_id),
        "cost_element_type_id": str(cost_element_type.cost_element_type_id),
        "department_code": "ENG",
        "department_name": "Engineering Department",
        "budget_bac": 10000.00,
        "revenue_plan": 15000.00,  # Exceeds WBE revenue_allocation of 10000.00
        "business_status": "active",
    }
    response = client.post(
        f"{settings.API_V1_STR}/cost-elements/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 400
    content = response.json()
    assert "exceeds WBE revenue allocation" in content["detail"]


def test_create_cost_element_exceeds_wbe_revenue_allocation_with_existing(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a cost element when sum of existing revenue_plan exceeds WBE limit."""
    from decimal import Decimal

    from app.models import WBE, WBECreate
    from tests.utils.project import create_random_project

    # Create WBE with specific revenue_allocation
    project = create_random_project(db)
    wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Test Machine",
        revenue_allocation=Decimal("20000.00"),
        status="designing",
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    cost_element_type = create_random_cost_element_type(db)

    # Create first cost element with revenue_plan
    first_ce_data = {
        "wbe_id": str(wbe.wbe_id),
        "cost_element_type_id": str(cost_element_type.cost_element_type_id),
        "department_code": "ENG1",
        "department_name": "Engineering 1",
        "budget_bac": 10000.00,
        "revenue_plan": 15000.00,
        "business_status": "active",
    }
    response1 = client.post(
        f"{settings.API_V1_STR}/cost-elements/",
        headers=superuser_token_headers,
        json=first_ce_data,
    )
    assert response1.status_code == 200

    # Try to create second cost element that would cause total to exceed limit
    second_ce_data = {
        "wbe_id": str(wbe.wbe_id),
        "cost_element_type_id": str(cost_element_type.cost_element_type_id),
        "department_code": "ENG2",
        "department_name": "Engineering 2",
        "budget_bac": 5000.00,
        "revenue_plan": 6000.00,  # Total would be 21000.00, exceeding 20000.00
        "business_status": "active",
    }
    response2 = client.post(
        f"{settings.API_V1_STR}/cost-elements/",
        headers=superuser_token_headers,
        json=second_ce_data,
    )
    assert response2.status_code == 400
    content = response2.json()
    assert "exceeds WBE revenue allocation" in content["detail"]


def test_update_cost_element_exceeds_wbe_revenue_allocation(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating a cost element revenue_plan that causes total to exceed limit."""
    from decimal import Decimal

    from app.models import WBE, WBECreate
    from tests.utils.project import create_random_project

    # Create WBE with specific revenue_allocation
    project = create_random_project(db)
    wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Test Machine",
        revenue_allocation=Decimal("30000.00"),
        status="designing",
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    cost_element_type = create_random_cost_element_type(db)

    # Create two cost elements within limit
    ce1_data = {
        "wbe_id": str(wbe.wbe_id),
        "cost_element_type_id": str(cost_element_type.cost_element_type_id),
        "department_code": "ENG1",
        "department_name": "Engineering 1",
        "budget_bac": 10000.00,
        "revenue_plan": 10000.00,
        "business_status": "active",
    }
    response1 = client.post(
        f"{settings.API_V1_STR}/cost-elements/",
        headers=superuser_token_headers,
        json=ce1_data,
    )
    assert response1.status_code == 200

    ce2_data = {
        "wbe_id": str(wbe.wbe_id),
        "cost_element_type_id": str(cost_element_type.cost_element_type_id),
        "department_code": "ENG2",
        "department_name": "Engineering 2",
        "budget_bac": 10000.00,
        "revenue_plan": 10000.00,
        "business_status": "active",
    }
    response2 = client.post(
        f"{settings.API_V1_STR}/cost-elements/",
        headers=superuser_token_headers,
        json=ce2_data,
    )
    assert response2.status_code == 200
    ce2_id = response2.json()["cost_element_id"]

    # Try to update second cost element to exceed limit
    update_data = {
        "revenue_plan": 25000.00,  # Total would be 35000.00, exceeding 30000.00
    }
    response3 = client.put(
        f"{settings.API_V1_STR}/cost-elements/{ce2_id}",
        headers=superuser_token_headers,
        json=update_data,
    )
    assert response3.status_code == 400
    content = response3.json()
    assert "exceeds WBE revenue allocation" in content["detail"]


def test_update_cost_element_within_wbe_revenue_allocation(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating a cost element revenue_plan that stays within limit."""
    from decimal import Decimal

    from app.models import WBE, WBECreate
    from tests.utils.project import create_random_project

    # Create WBE with specific revenue_allocation
    project = create_random_project(db)
    wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Test Machine",
        revenue_allocation=Decimal("30000.00"),
        status="designing",
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    cost_element_type = create_random_cost_element_type(db)

    # Create cost element
    ce_data = {
        "wbe_id": str(wbe.wbe_id),
        "cost_element_type_id": str(cost_element_type.cost_element_type_id),
        "department_code": "ENG",
        "department_name": "Engineering",
        "budget_bac": 10000.00,
        "revenue_plan": 15000.00,
        "business_status": "active",
    }
    response1 = client.post(
        f"{settings.API_V1_STR}/cost-elements/",
        headers=superuser_token_headers,
        json=ce_data,
    )
    assert response1.status_code == 200
    ce_id = response1.json()["cost_element_id"]

    # Update to a value still within limit
    update_data = {
        "revenue_plan": 10000.00,  # Still within 30000.00 limit
    }
    response2 = client.put(
        f"{settings.API_V1_STR}/cost-elements/{ce_id}",
        headers=superuser_token_headers,
        json=update_data,
    )
    assert response2.status_code == 200
    content = response2.json()
    assert float(content["revenue_plan"]) == 10000.00


def test_create_cost_element_at_wbe_revenue_allocation_limit(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a cost element with revenue_plan exactly at WBE limit should succeed."""
    from decimal import Decimal

    from app.models import WBE, WBECreate
    from tests.utils.project import create_random_project

    # Create WBE with specific revenue_allocation
    project = create_random_project(db)
    wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Test Machine",
        revenue_allocation=Decimal("10000.00"),
        status="designing",
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    cost_element_type = create_random_cost_element_type(db)

    # Create cost element with revenue_plan exactly at limit
    ce_data = {
        "wbe_id": str(wbe.wbe_id),
        "cost_element_type_id": str(cost_element_type.cost_element_type_id),
        "department_code": "ENG",
        "department_name": "Engineering",
        "budget_bac": 10000.00,
        "revenue_plan": 10000.00,  # Exactly at limit
        "business_status": "active",
    }
    response = client.post(
        f"{settings.API_V1_STR}/cost-elements/",
        headers=superuser_token_headers,
        json=ce_data,
    )
    assert response.status_code == 200
    content = response.json()
    assert float(content["revenue_plan"]) == 10000.00


def test_create_cost_element_creates_initial_budget_allocation(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test that creating a cost element automatically creates an initial BudgetAllocation record."""
    from decimal import Decimal

    from app.models import WBE, WBECreate
    from tests.utils.project import create_random_project
    # Note: created_by_id will be set to the current user making the API call
    # We verify it's set but don't check the exact value since we don't have direct access

    # Create WBE
    project = create_random_project(db)
    wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Test Machine",
        revenue_allocation=Decimal("50000.00"),
        status="designing",
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    cost_element_type = create_random_cost_element_type(db)

    # Create cost element via API
    ce_data = {
        "wbe_id": str(wbe.wbe_id),
        "cost_element_type_id": str(cost_element_type.cost_element_type_id),
        "department_code": "ENG",
        "department_name": "Engineering",
        "budget_bac": 15000.00,
        "revenue_plan": 18000.00,
        "business_status": "active",
    }
    response = client.post(
        f"{settings.API_V1_STR}/cost-elements/",
        headers=superuser_token_headers,
        json=ce_data,
    )
    assert response.status_code == 200
    content = response.json()
    cost_element_id = content["cost_element_id"]

    # Query for BudgetAllocation record
    statement = select(BudgetAllocation).where(
        BudgetAllocation.cost_element_id == uuid.UUID(cost_element_id)
    )
    budget_allocations = db.exec(statement).all()

    # Verify BudgetAllocation was created
    assert len(budget_allocations) == 1, "Expected exactly one BudgetAllocation record"

    budget = budget_allocations[0]
    assert budget.budget_amount == Decimal("15000.00")
    assert budget.revenue_amount == Decimal("18000.00")
    assert budget.allocation_type == "initial"
    assert budget.cost_element_id == uuid.UUID(cost_element_id)
    assert budget.allocation_date == date.today()
    # Note: created_by_id check requires knowing which user made the API call
    # We can verify it's set but not the exact value without more setup
    assert budget.created_by_id is not None


def test_update_cost_element_budget_creates_new_budget_allocation(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test that updating cost element budget_bac creates a new BudgetAllocation record."""
    from decimal import Decimal

    from app.models import WBE, WBECreate
    from tests.utils.project import create_random_project

    # Create cost element
    project = create_random_project(db)
    wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Test Machine",
        revenue_allocation=Decimal("50000.00"),
        status="designing",
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    cost_element_type = create_random_cost_element_type(db)

    # Create cost element
    ce_data = {
        "wbe_id": str(wbe.wbe_id),
        "cost_element_type_id": str(cost_element_type.cost_element_type_id),
        "department_code": "ENG",
        "department_name": "Engineering",
        "budget_bac": 10000.00,
        "revenue_plan": 12000.00,
        "business_status": "active",
    }
    response1 = client.post(
        f"{settings.API_V1_STR}/cost-elements/",
        headers=superuser_token_headers,
        json=ce_data,
    )
    assert response1.status_code == 200
    created_payload = response1.json()
    cost_element_id = created_payload["cost_element_id"]
    cost_entity_id = uuid.UUID(created_payload["entity_id"])

    # Verify initial BudgetAllocation exists
    statement = select(BudgetAllocation).where(
        BudgetAllocation.cost_element_id == uuid.UUID(cost_element_id)
    )
    initial_budgets = db.exec(statement).all()
    assert len(initial_budgets) == 1

    # Update budget_bac
    update_data = {
        "budget_bac": 15000.00,  # Changed from 10000.00
    }
    response2 = client.put(
        f"{settings.API_V1_STR}/cost-elements/{cost_element_id}",
        headers=superuser_token_headers,
        json=update_data,
    )
    assert response2.status_code == 200

    # Verify new BudgetAllocation record was created
    ce_ids = [
        ce.cost_element_id
        for ce in db.exec(
            select(CostElement).where(CostElement.entity_id == cost_entity_id)
        ).all()
    ]
    updated_budgets = db.exec(
        select(BudgetAllocation).where(BudgetAllocation.cost_element_id.in_(ce_ids))
    ).all()
    assert (
        len(updated_budgets) == 2
    ), "Expected two BudgetAllocation records (initial + update)"

    # Find the new record (should have budget_amount = 15000.00)
    new_budget = next(
        (b for b in updated_budgets if b.budget_amount == Decimal("15000.00")), None
    )
    assert (
        new_budget is not None
    ), "New BudgetAllocation with updated budget_amount not found"
    assert new_budget.allocation_type == "update"
    assert new_budget.allocation_date == date.today()


def test_update_cost_element_revenue_creates_new_budget_allocation(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test that updating cost element revenue_plan creates a new BudgetAllocation record."""
    from decimal import Decimal

    from app.models import WBE, WBECreate
    from tests.utils.project import create_random_project

    # Create cost element
    project = create_random_project(db)
    wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Test Machine",
        revenue_allocation=Decimal("50000.00"),
        status="designing",
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    cost_element_type = create_random_cost_element_type(db)

    # Create cost element
    ce_data = {
        "wbe_id": str(wbe.wbe_id),
        "cost_element_type_id": str(cost_element_type.cost_element_type_id),
        "department_code": "ENG",
        "department_name": "Engineering",
        "budget_bac": 10000.00,
        "revenue_plan": 12000.00,
        "business_status": "active",
    }
    response1 = client.post(
        f"{settings.API_V1_STR}/cost-elements/",
        headers=superuser_token_headers,
        json=ce_data,
    )
    assert response1.status_code == 200
    created_payload = response1.json()
    cost_element_id = created_payload["cost_element_id"]
    cost_entity_id = uuid.UUID(created_payload["entity_id"])

    # Update revenue_plan
    update_data = {
        "revenue_plan": 15000.00,  # Changed from 12000.00
    }
    response2 = client.put(
        f"{settings.API_V1_STR}/cost-elements/{cost_element_id}",
        headers=superuser_token_headers,
        json=update_data,
    )
    assert response2.status_code == 200

    # Verify new BudgetAllocation record was created
    ce_ids = [
        ce.cost_element_id
        for ce in db.exec(
            select(CostElement).where(CostElement.entity_id == cost_entity_id)
        ).all()
    ]
    budgets = db.exec(
        select(BudgetAllocation).where(BudgetAllocation.cost_element_id.in_(ce_ids))
    ).all()
    assert len(budgets) == 2, "Expected two BudgetAllocation records (initial + update)"

    # Find the new record (should have revenue_amount = 15000.00)
    new_budget = next(
        (b for b in budgets if b.revenue_amount == Decimal("15000.00")), None
    )
    assert (
        new_budget is not None
    ), "New BudgetAllocation with updated revenue_amount not found"
    assert new_budget.allocation_type == "update"


def test_update_cost_element_both_budget_and_revenue_creates_one_budget_allocation(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test that updating both budget_bac and revenue_plan in same update creates one BudgetAllocation record."""
    from decimal import Decimal

    from app.models import WBE, WBECreate
    from tests.utils.project import create_random_project

    # Create cost element
    project = create_random_project(db)
    wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Test Machine",
        revenue_allocation=Decimal("50000.00"),
        status="designing",
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    cost_element_type = create_random_cost_element_type(db)

    # Create cost element
    ce_data = {
        "wbe_id": str(wbe.wbe_id),
        "cost_element_type_id": str(cost_element_type.cost_element_type_id),
        "department_code": "ENG",
        "department_name": "Engineering",
        "budget_bac": 10000.00,
        "revenue_plan": 12000.00,
        "business_status": "active",
    }
    response1 = client.post(
        f"{settings.API_V1_STR}/cost-elements/",
        headers=superuser_token_headers,
        json=ce_data,
    )
    assert response1.status_code == 200
    created_payload = response1.json()
    cost_element_id = created_payload["cost_element_id"]
    cost_entity_id = uuid.UUID(created_payload["entity_id"])

    # Update both budget_bac and revenue_plan
    update_data = {
        "budget_bac": 15000.00,
        "revenue_plan": 18000.00,
    }
    response2 = client.put(
        f"{settings.API_V1_STR}/cost-elements/{cost_element_id}",
        headers=superuser_token_headers,
        json=update_data,
    )
    assert response2.status_code == 200

    # Verify exactly one new BudgetAllocation record was created (total = 2: initial + update)
    ce_ids = [
        ce.cost_element_id
        for ce in db.exec(
            select(CostElement).where(CostElement.entity_id == cost_entity_id)
        ).all()
    ]
    budgets = db.exec(
        select(BudgetAllocation).where(BudgetAllocation.cost_element_id.in_(ce_ids))
    ).all()
    assert (
        len(budgets) == 2
    ), "Expected exactly two BudgetAllocation records (initial + one update)"

    # Find the update record
    update_budget = next((b for b in budgets if b.allocation_type == "update"), None)
    assert update_budget is not None
    assert update_budget.budget_amount == Decimal("15000.00")
    assert update_budget.revenue_amount == Decimal("18000.00")


def test_read_cost_elements_with_view_mode_branch_only(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test that read_cost_elements with view_mode='branch-only' returns only branch entities."""
    from decimal import Decimal

    from app import crud
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

    # Create project
    email = f"pm_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    pm_user = crud.create_user(session=db, user_create=user_in)

    project_in = ProjectCreate(
        project_name="View Mode Test Project",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date.today(),
        planned_completion_date=date.today() + timedelta(days=365),
        project_manager_id=pm_user.id,
        status="active",
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    branch = "co-001"

    # Create WBE
    wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Test WBE",
        revenue_allocation=Decimal("50000.00"),
        status="designing",
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    # Create CostElementType
    cet_in = CostElementTypeCreate(
        type_code=f"test_{uuid.uuid4().hex[:6]}",
        type_name="Test Type",
        category_type="engineering_mechanical",
        display_order=1,
        is_active=True,
    )
    cet = CostElementType.model_validate(cet_in)
    db.add(cet)
    db.commit()
    db.refresh(cet)

    # Create cost element in main branch
    main_ce_in = CostElementCreate(
        wbe_id=wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="MAIN",
        department_name="Main Department",
        budget_bac=Decimal("10000.00"),
        revenue_plan=Decimal("12000.00"),
    )
    main_ce = CostElement.model_validate(main_ce_in)
    db.add(main_ce)
    db.commit()
    db.refresh(main_ce)

    # Create WBE in branch
    branch_wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Branch WBE",
        revenue_allocation=Decimal("30000.00"),
        status="designing",
    )
    branch_wbe = WBE.model_validate(branch_wbe_in)
    branch_wbe.branch = branch
    db.add(branch_wbe)
    db.commit()
    db.refresh(branch_wbe)

    # Create cost element in branch
    branch_ce_in = CostElementCreate(
        wbe_id=branch_wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="BRANCH",
        department_name="Branch Department",
        budget_bac=Decimal("20000.00"),
        revenue_plan=Decimal("24000.00"),
    )
    branch_ce = CostElement.model_validate(branch_ce_in)
    branch_ce.branch = branch
    db.add(branch_ce)
    db.commit()

    # Test branch-only view mode
    response = client.get(
        f"{settings.API_V1_STR}/cost-elements/?wbe_id={branch_wbe.wbe_id}&branch={branch}&view_mode=branch-only",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    # Should only return branch cost element
    assert content["count"] == 1
    assert len(content["data"]) == 1
    assert content["data"][0]["department_code"] == "BRANCH"
    assert content["data"][0]["branch"] == branch


def test_read_cost_elements_with_view_mode_merged_default(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test that read_cost_elements defaults to view_mode='merged' and includes change_status."""
    from decimal import Decimal

    from app import crud
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

    # Create project
    email = f"pm_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    pm_user = crud.create_user(session=db, user_create=user_in)

    project_in = ProjectCreate(
        project_name="Merged View Test Project",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date.today(),
        planned_completion_date=date.today() + timedelta(days=365),
        project_manager_id=pm_user.id,
        status="active",
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    branch = "co-001"

    # Create WBE in main
    main_wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Main WBE",
        revenue_allocation=Decimal("50000.00"),
        status="designing",
    )
    main_wbe = WBE.model_validate(main_wbe_in)
    db.add(main_wbe)
    db.commit()
    db.refresh(main_wbe)

    # Create CostElementType
    cet_in = CostElementTypeCreate(
        type_code=f"test_{uuid.uuid4().hex[:6]}",
        type_name="Test Type",
        category_type="engineering_mechanical",
        display_order=1,
        is_active=True,
    )
    cet = CostElementType.model_validate(cet_in)
    db.add(cet)
    db.commit()
    db.refresh(cet)

    # Create cost element in main branch
    main_ce_in = CostElementCreate(
        wbe_id=main_wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="MAIN",
        department_name="Main Department",
        budget_bac=Decimal("10000.00"),
        revenue_plan=Decimal("12000.00"),
    )
    main_ce = CostElement.model_validate(main_ce_in)
    db.add(main_ce)
    db.commit()
    db.refresh(main_ce)

    # Create WBE in branch
    branch_wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Branch WBE",
        revenue_allocation=Decimal("30000.00"),
        status="designing",
    )
    branch_wbe = WBE.model_validate(branch_wbe_in)
    branch_wbe.branch = branch
    db.add(branch_wbe)
    db.commit()
    db.refresh(branch_wbe)

    # Create cost element in branch
    branch_ce_in = CostElementCreate(
        wbe_id=branch_wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="BRANCH",
        department_name="Branch Department",
        budget_bac=Decimal("20000.00"),
        revenue_plan=Decimal("24000.00"),
    )
    branch_ce = CostElement.model_validate(branch_ce_in)
    branch_ce.branch = branch
    db.add(branch_ce)
    db.commit()
    db.refresh(branch_ce)

    # Test merged view mode (default, no view_mode parameter) - filter by main WBE
    response = client.get(
        f"{settings.API_V1_STR}/cost-elements/?wbe_id={main_wbe.wbe_id}&branch={branch}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    # Should return main cost element with unchanged status
    assert content["count"] == 1
    assert len(content["data"]) == 1
    assert content["data"][0]["department_code"] == "MAIN"

    # Check that change_status is included in merged view
    assert (
        "change_status" in content["data"][0]
    ), "change_status should be included in merged view"
    assert content["data"][0]["change_status"] == "unchanged"

    # Test explicit merged view mode - filter by branch WBE
    response2 = client.get(
        f"{settings.API_V1_STR}/cost-elements/?wbe_id={branch_wbe.wbe_id}&branch={branch}&view_mode=merged",
        headers=superuser_token_headers,
    )
    assert response2.status_code == 200
    content2 = response2.json()
    assert content2["count"] == 1
    assert len(content2["data"]) == 1
    assert content2["data"][0]["department_code"] == "BRANCH"
    assert content2["data"][0]["change_status"] == "created"


def test_read_cost_element_with_view_mode_merged(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test that read_cost_element (single entity) supports view_mode parameter."""
    from decimal import Decimal

    from app import crud
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

    # Create project
    email = f"pm_{uuid.uuid4().hex[:8]}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    pm_user = crud.create_user(session=db, user_create=user_in)

    project_in = ProjectCreate(
        project_name="Single CE Test Project",
        customer_name="Test Customer",
        contract_value=Decimal("100000.00"),
        start_date=date.today(),
        planned_completion_date=date.today() + timedelta(days=365),
        project_manager_id=pm_user.id,
        status="active",
    )
    project = Project.model_validate(project_in)
    db.add(project)
    db.commit()
    db.refresh(project)

    branch = "co-001"

    # Create WBE
    wbe_in = WBECreate(
        project_id=project.project_id,
        machine_type="Test WBE",
        revenue_allocation=Decimal("50000.00"),
        status="designing",
    )
    wbe = WBE.model_validate(wbe_in)
    db.add(wbe)
    db.commit()
    db.refresh(wbe)

    # Create CostElementType
    cet_in = CostElementTypeCreate(
        type_code=f"test_{uuid.uuid4().hex[:6]}",
        type_name="Test Type",
        category_type="engineering_mechanical",
        display_order=1,
        is_active=True,
    )
    cet = CostElementType.model_validate(cet_in)
    db.add(cet)
    db.commit()
    db.refresh(cet)

    # Create cost element in main branch
    main_ce_in = CostElementCreate(
        wbe_id=wbe.wbe_id,
        cost_element_type_id=cet.cost_element_type_id,
        department_code="MAIN",
        department_name="Main Department",
        budget_bac=Decimal("10000.00"),
        revenue_plan=Decimal("12000.00"),
    )
    main_ce = CostElement.model_validate(main_ce_in)
    db.add(main_ce)
    db.commit()
    db.refresh(main_ce)

    # Test single cost element with merged view mode
    response = client.get(
        f"{settings.API_V1_STR}/cost-elements/{main_ce.cost_element_id}?branch={branch}&view_mode=merged",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["department_code"] == "MAIN"
    # change_status should be included when view_mode='merged'
    assert "change_status" in content, "change_status should be included in merged view"
    assert content["change_status"] == "unchanged"
