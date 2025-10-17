import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from src.api import main
from src.api.main import app
import src.api.routes as routes
from src.config import get_settings
from pathlib import Path


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_lifespan_loads_graph_and_data(monkeypatch, tmp_path):
    graph_path = tmp_path / "transport_graph.gml"
    stops_path = tmp_path / "stops.csv"
    routes_path = tmp_path / "routes.csv"

    graph_path.touch()
    stops_path.write_text("stop_id,stop_name,stop_lat,stop_lon\nA,Stop A,0.0,0.0")
    routes_path.write_text(
        "route_id,route_short_name,route_long_name,route_type\nR1,R,Route R,3"
    )

    # --- Mock settings ---
    settings = get_settings()
    monkeypatch.setattr("src.api.main.settings", settings)
    monkeypatch.setattr(settings, "processed_data_dir", tmp_path)

    # --- Mock builder ---
    mock_graph = MagicMock(name="graph")
    mock_builder = MagicMock()
    mock_builder.load_graph.return_value = mock_graph
    monkeypatch.setattr("src.api.main.TransportGraphBuilder", lambda: mock_builder)

    async with main.lifespan(app=MagicMock()):
        assert routes.route_planner is not None
        assert routes.stops_df is not None
        assert routes.routes_df is not None
        mock_builder.load_graph.assert_called_once_with(graph_path)
        mock_builder.save_graph.assert_not_called()


@pytest.mark.asyncio
async def test_health_with_mocked_graph(monkeypatch):
    """Test le endpoint /health avec les méthodes du graphe mockées."""
    fake_graph = MagicMock()
    fake_graph.number_of_nodes.return_value = 42
    fake_graph.number_of_edges.return_value = 99

    fake_planner = MagicMock()
    fake_planner.graph = fake_graph

    monkeypatch.setattr(routes, "route_planner", fake_planner)
    monkeypatch.setattr(main.settings, "environment", "test")

    response = await main.health()

    assert response.status == "healthy"
    assert response.environment == "test"
    assert response.graph_loaded is True
    assert response.num_nodes == 42
    assert response.num_edges == 99

    fake_graph.number_of_nodes.assert_called_once()
    fake_graph.number_of_edges.assert_called_once()


@pytest.mark.asyncio
async def test_lifespan_builds_graph(monkeypatch, tmp_path):
    graph_path = tmp_path / "transport_graph.gml"
    stops_path = tmp_path / "stops.csv"
    routes_path = tmp_path / "routes.csv"

    stops_path.write_text("stop_id,stop_name,stop_lat,stop_lon\nA,Stop A,0.0,0.0")
    routes_path.write_text(
        "route_id,route_short_name,route_long_name,route_type\nR1,R,Route R,3"
    )

    # --- Mock settings ---
    settings = get_settings()
    monkeypatch.setattr("src.api.main.settings", settings)
    monkeypatch.setattr(settings, "processed_data_dir", tmp_path)

    # --- Mock builder ---
    mock_graph = MagicMock(name="graph")
    mock_builder = MagicMock()
    mock_builder.build_graph.return_value = mock_graph
    monkeypatch.setattr("src.api.main.TransportGraphBuilder", lambda: mock_builder)

    async with main.lifespan(app=MagicMock()):
        mock_builder.build_graph.assert_called_once()
        mock_builder.save_graph.assert_called_once_with(graph_path)
        assert routes.route_planner is not None
        assert routes.stops_df is not None
        assert routes.routes_df is not None


@pytest.mark.asyncio
async def test_lifespan_handles_exception(monkeypatch, tmp_path):
    # --- Mock settings ---
    settings = get_settings()
    monkeypatch.setattr("src.api.main.settings", settings)
    monkeypatch.setattr(settings, "processed_data_dir", tmp_path)

    mock_builder = MagicMock()
    mock_builder.load_graph.side_effect = Exception("mocked failure")
    monkeypatch.setattr("src.api.main.TransportGraphBuilder", lambda: mock_builder)

    graph_path = tmp_path / "transport_graph.gml"
    graph_path.touch()

    async with main.lifespan(app=MagicMock()):
        assert routes.route_planner is None


@pytest.mark.asyncio
async def test_root_fallback(monkeypatch):
    client = TestClient(app)

    monkeypatch.setattr(Path, "exists", lambda self: False)

    response = client.get("/")
    assert response.status_code == 200
    assert "DiviaMobilités Transport Planner API" in response.text
    assert "<title>DiviaMobilités Transport Planner</title>" in response.text
    assert "/docs" in response.text
    assert "/health" in response.text
