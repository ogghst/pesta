"""Tests for Cost Registrations API routes."""
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.cost_element import create_random_cost_element
from tests.utils.cost_registration import create_random_cost_registration


def test_create_cost_registration(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a cost registration."""
    cost_element = create_random_cost_element(db)

    data = {
        "cost_element_id": str(cost_element.cost_element_id),
        "registration_date": "2024-02-15",
        "amount": "1500.00",
        "cost_category": "labor",
        "description": "Test cost registration",
        "is_quality_cost": False,
    }
    response = client.post(
        f"{settings.API_V1_STR}/cost-registrations/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["amount"] == "1500.00"
    assert content["cost_category"] == "labor"
    assert content["description"] == "Test cost registration"
    assert content["cost_element_id"] == str(cost_element.cost_element_id)
    assert "cost_registration_id" in content
    assert "created_by_id" in content


def test_create_cost_registration_invalid_cost_element(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,  # noqa: ARG001
) -> None:
    """Test creating a cost registration with invalid cost_element_id."""
    data = {
        "cost_element_id": str(uuid.uuid4()),
        "registration_date": "2024-02-15",
        "amount": "1500.00",
        "cost_category": "labor",
        "description": "Test cost registration",
        "is_quality_cost": False,
    }
    response = client.post(
        f"{settings.API_V1_STR}/cost-registrations/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Cost element not found"


def test_create_cost_registration_invalid_category(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a cost registration with invalid cost category."""
    cost_element = create_random_cost_element(db)

    data = {
        "cost_element_id": str(cost_element.cost_element_id),
        "registration_date": "2024-02-15",
        "amount": "1500.00",
        "cost_category": "invalid_category",
        "description": "Test cost registration",
        "is_quality_cost": False,
    }
    response = client.post(
        f"{settings.API_V1_STR}/cost-registrations/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 400
    content = response.json()
    assert "Invalid cost category" in content["detail"]


def test_create_cost_registration_invalid_amount(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a cost registration with invalid amount."""
    cost_element = create_random_cost_element(db)

    data = {
        "cost_element_id": str(cost_element.cost_element_id),
        "registration_date": "2024-02-15",
        "amount": "0.00",
        "cost_category": "labor",
        "description": "Test cost registration",
        "is_quality_cost": False,
    }
    response = client.post(
        f"{settings.API_V1_STR}/cost-registrations/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Amount must be greater than zero"


def test_read_cost_registration(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test reading a single cost registration."""
    cost_registration = create_random_cost_registration(db)
    response = client.get(
        f"{settings.API_V1_STR}/cost-registrations/{cost_registration.cost_registration_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["cost_registration_id"] == str(
        cost_registration.cost_registration_id
    )
    assert content["amount"] == str(cost_registration.amount)


def test_read_cost_registrations_list(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test reading list of cost registrations."""
    cost_element = create_random_cost_element(db)
    cr1 = create_random_cost_registration(
        db, cost_element_id=cost_element.cost_element_id
    )
    cr2 = create_random_cost_registration(
        db, cost_element_id=cost_element.cost_element_id
    )

    response = client.get(
        f"{settings.API_V1_STR}/cost-registrations/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert "count" in content
    assert content["count"] >= 2

    # Verify the created registrations are in the response
    registration_ids = [cr["cost_registration_id"] for cr in content["data"]]
    assert str(cr1.cost_registration_id) in registration_ids
    assert str(cr2.cost_registration_id) in registration_ids


def test_read_cost_registrations_filtered_by_cost_element(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test reading cost registrations filtered by cost element ID."""
    cost_element1 = create_random_cost_element(db)
    cost_element2 = create_random_cost_element(db)

    cr1 = create_random_cost_registration(
        db, cost_element_id=cost_element1.cost_element_id
    )
    cr2 = create_random_cost_registration(
        db, cost_element_id=cost_element1.cost_element_id
    )
    cr3 = create_random_cost_registration(
        db, cost_element_id=cost_element2.cost_element_id
    )

    # Filter by cost_element1
    response = client.get(
        f"{settings.API_V1_STR}/cost-registrations/",
        params={"cost_element_id": str(cost_element1.cost_element_id)},
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["count"] == 2

    registration_ids = [cr["cost_registration_id"] for cr in content["data"]]
    assert str(cr1.cost_registration_id) in registration_ids
    assert str(cr2.cost_registration_id) in registration_ids
    assert str(cr3.cost_registration_id) not in registration_ids


def test_update_cost_registration(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating a cost registration."""
    cost_registration = create_random_cost_registration(db)

    data = {
        "amount": "2000.00",
        "description": "Updated description",
    }
    response = client.put(
        f"{settings.API_V1_STR}/cost-registrations/{cost_registration.cost_registration_id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["amount"] == "2000.00"
    assert content["description"] == "Updated description"
    assert content["cost_category"] == cost_registration.cost_category  # Unchanged


def test_update_cost_registration_invalid_category(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating a cost registration with invalid category."""
    cost_registration = create_random_cost_registration(db)

    data = {
        "cost_category": "invalid_category",
    }
    response = client.put(
        f"{settings.API_V1_STR}/cost-registrations/{cost_registration.cost_registration_id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 400
    content = response.json()
    assert "Invalid cost category" in content["detail"]


def test_update_cost_registration_invalid_amount(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating a cost registration with invalid amount."""
    cost_registration = create_random_cost_registration(db)

    data = {
        "amount": "-100.00",
    }
    response = client.put(
        f"{settings.API_V1_STR}/cost-registrations/{cost_registration.cost_registration_id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 400
    content = response.json()
    assert "Amount must be greater than zero" in content["detail"]


def test_delete_cost_registration(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test deleting a cost registration."""
    cost_registration = create_random_cost_registration(db)

    response = client.delete(
        f"{settings.API_V1_STR}/cost-registrations/{cost_registration.cost_registration_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Cost registration deleted successfully"

    # Verify it's deleted
    response = client.get(
        f"{settings.API_V1_STR}/cost-registrations/{cost_registration.cost_registration_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404


def test_read_cost_registration_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test reading a non-existent cost registration."""
    response = client.get(
        f"{settings.API_V1_STR}/cost-registrations/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404


def test_create_cost_registration_all_categories(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating cost registrations with all valid categories."""
    cost_element = create_random_cost_element(db)
    valid_categories = ["labor", "materials", "subcontractors"]

    for category in valid_categories:
        data = {
            "cost_element_id": str(cost_element.cost_element_id),
            "registration_date": "2024-02-15",
            "amount": "1000.00",
            "cost_category": category,
            "description": f"Test {category} cost",
            "is_quality_cost": False,
        }
        response = client.post(
            f"{settings.API_V1_STR}/cost-registrations/",
            headers=superuser_token_headers,
            json=data,
        )
        assert response.status_code == 200
        content = response.json()
        assert content["cost_category"] == category
