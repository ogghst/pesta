"""Tests for Cost Categories API routes."""
from fastapi.testclient import TestClient


def test_read_cost_categories(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test reading cost categories."""
    response = client.get(
        "/api/v1/cost-categories/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data
    assert data["count"] == 3
    assert len(data["data"]) == 3
    categories = data["data"]
    category_names = [cat["name"] for cat in categories]
    assert "labor" in category_names
    assert "materials" in category_names
    assert "subcontractors" in category_names


def test_read_cost_categories_unauthorized(client: TestClient) -> None:
    """Test reading cost categories without authentication."""
    response = client.get("/api/v1/cost-categories/")
    assert response.status_code == 401


def test_cost_categories_response_format(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test cost categories response format."""
    response = client.get(
        "/api/v1/cost-categories/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    # Verify structure
    assert "data" in data
    assert "count" in data
    # Verify each category has required fields
    for category in data["data"]:
        assert "name" in category
        assert "code" in category
        assert isinstance(category["name"], str)
        assert isinstance(category["code"], str)
