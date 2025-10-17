import pytest
import pandas as pd
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

import src.api.routes as routing


@pytest.fixture(autouse=True)
def reset_globals(monkeypatch):
    routing.route_planner = None
    routing.stops_df = None
    routing.routes_df = None

    dummy_counter = MagicMock()
    dummy_timer = MagicMock()
    dummy_timer.time.return_value.__enter__.return_value = None
    dummy_timer.time.return_value.__exit__.return_value = None
    dummy_counter.labels.return_value = dummy_counter
    dummy_timer.labels.return_value = dummy_timer

    monkeypatch.setattr(routing, "api_requests_total", dummy_counter)
    monkeypatch.setattr(routing, "api_request_duration", dummy_timer)

    yield


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(routing.router)
    return TestClient(app)


@pytest.fixture
def fake_planner(monkeypatch):
    planner = MagicMock()
    routing.route_planner = planner
    return planner


def test_get_planner_not_initialized():
    routing.route_planner = None
    with pytest.raises(HTTPException) as e:
        routing.get_planner()
    assert e.value.status_code == 503


def test_get_planner_ok(fake_planner):
    assert routing.get_planner() is fake_planner


def test_calculate_route_success(client, fake_planner):
    fake_planner.find_shortest_path.return_value = (["A", "B"], 10)
    fake_planner.get_path_details.return_value = [
        {
            "stop_id": "A",
            "stop_name": "Alpha",
            "lat": 1.0,
            "lon": 2.0,
            "sequence": 1,
            "is_transfer": False,
        },
        {
            "stop_id": "B",
            "stop_name": "Beta",
            "lat": 3.0,
            "lon": 4.0,
            "sequence": 2,
            "is_transfer": True,
        },
    ]

    body = {"departure": "A", "arrival": "B"}
    response = client.post("/api/v1/route", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["origin"] == "A"
    assert data["destination"] == "B"
    assert data["num_transfers"] == 1


def test_calculate_route_not_found(client, fake_planner):
    fake_planner.find_shortest_path.return_value = None
    body = {"departure": "A", "arrival": "B"}
    response = client.post("/api/v1/route", json=body)
    assert response.status_code == 404
    assert "No route found" in response.text


def test_calculate_alternative_routes_success(client, fake_planner):
    fake_planner.find_alternative_routes.return_value = [
        (["A", "B"], 10),
        (["A", "C", "B"], 15),
    ]
    fake_planner.get_path_details.side_effect = [
        [
            {
                "stop_id": "A",
                "stop_name": "Alpha",
                "lat": 1.0,
                "lon": 2.0,
                "sequence": 1,
                "is_transfer": False,
            },
            {
                "stop_id": "B",
                "stop_name": "Beta",
                "lat": 3.0,
                "lon": 4.0,
                "sequence": 2,
                "is_transfer": True,
            },
        ],
        [
            {
                "stop_id": "A",
                "stop_name": "Alpha",
                "lat": 1.0,
                "lon": 2.0,
                "sequence": 1,
                "is_transfer": False,
            },
            {
                "stop_id": "C",
                "stop_name": "Gamma",
                "lat": 5.0,
                "lon": 6.0,
                "sequence": 2,
                "is_transfer": False,
            },
            {
                "stop_id": "B",
                "stop_name": "Beta",
                "lat": 3.0,
                "lon": 4.0,
                "sequence": 3,
                "is_transfer": False,
            },
        ],
    ]

    body = {"departure": "A", "arrival": "B", "alternatives": 2}
    response = client.post("/api/v1/route/alternatives", json=body)
    assert response.status_code == 200
    data = response.json()
    assert len(data["routes"]) == 2


def test_calculate_alternative_routes_not_found(client, fake_planner):
    fake_planner.find_alternative_routes.return_value = []
    body = {"departure": "A", "arrival": "B", "alternatives": 2}
    response = client.post("/api/v1/route/alternatives", json=body)
    assert response.status_code == 404
    assert "No routes found" in response.text


def test_get_stops_not_loaded(client):
    routing.stops_df = None
    response = client.get("/api/v1/stops")
    assert response.status_code == 503


def test_get_stops_with_data_and_search(client):
    routing.stops_df = pd.DataFrame(
        [
            {"stop_id": "A", "stop_name": "Alpha", "stop_lat": 1.0, "stop_lon": 2.0},
            {"stop_id": "B", "stop_name": "Beta", "stop_lat": 3.0, "stop_lon": 4.0},
        ]
    )
    response = client.get("/api/v1/stops", params={"search": "alp", "limit": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["stops"][0]["stop_name"] == "Alpha"


def test_get_routes_not_loaded(client):
    routing.routes_df = None
    response = client.get("/api/v1/routes")
    assert response.status_code == 503


def test_get_routes_with_data(client):
    routing.routes_df = pd.DataFrame(
        [
            {
                "route_id": "R1",
                "route_short_name": "S1",
                "route_long_name": "L1",
                "route_type": 3,
            }
        ]
    )
    response = client.get("/api/v1/routes")
    assert response.status_code == 200
    data = response.json()
    assert data["routes"][0]["route_id"] == "R1"


def test_get_nearby_stops_not_loaded(client, fake_planner):
    routing.stops_df = None
    response = client.get("/api/v1/stops/A/nearby")
    assert response.status_code == 503


def test_get_nearby_stops_success(client, fake_planner):
    routing.stops_df = pd.DataFrame(
        [
            {"stop_id": "A", "stop_name": "Alpha", "stop_lat": 1.0, "stop_lon": 2.0},
            {"stop_id": "B", "stop_name": "Beta", "stop_lat": 3.0, "stop_lon": 4.0},
            {"stop_id": "C", "stop_name": "Gamma", "stop_lat": 5.0, "stop_lon": 6.0},
        ]
    )
    fake_planner.get_nearby_stops.return_value = ["A", "B"]
    response = client.get("/api/v1/stops/A/nearby?max_distance=3")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert any(stop["stop_id"] == "B" for stop in data["stops"])
