import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.cost_element import create_random_cost_element
from tests.utils.cost_element_type import create_random_cost_element_type
from tests.utils.wbe import create_random_wbe


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
        "status": "active",
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
        "status": "active",
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
        "status": "active",
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


def test_update_cost_element(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating a cost element."""
    cost_element = create_random_cost_element(db)
    data = {"department_name": "Updated Department Name", "status": "completed"}
    response = client.put(
        f"{settings.API_V1_STR}/cost-elements/{cost_element.cost_element_id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["department_name"] == data["department_name"]
    assert content["status"] == data["status"]
    assert content["cost_element_id"] == str(cost_element.cost_element_id)


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
