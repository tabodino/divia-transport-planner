"""Tests for API endpoints."""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "DiviaMobilités" in response.text


def test_health():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "environment" in data


def test_get_stops():
    """Test get stops endpoint."""
    response = client.get("/api/v1/stops?limit=10")
    assert response.status_code in [200, 503]  # 503 if data not loaded

    if response.status_code == 200:
        data = response.json()
        assert "stops" in data
        assert "total" in data


def test_get_routes():
    """Test get routes endpoint."""
    response = client.get("/api/v1/routes")
    assert response.status_code in [200, 503]  # 503 if data not loaded

    if response.status_code == 200:
        data = response.json()
        assert "routes" in data
        assert "total" in data


def test_calculate_route_invalid():
    """Test route calculation with invalid stops."""
    response = client.post(
        "/api/v1/route", json={"departure": "INVALID_1", "arrival": "INVALID_2"}
    )
    # Should return 404 or 503 depending on graph state
    assert response.status_code in [404, 503]


def test_metrics():
    """Test Prometheus metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
