import pytest
import networkx as nx
from src.graph.router import RoutePlanner


@pytest.fixture
def simple_graph():
    G = nx.MultiDiGraph()
    G.add_node("A", name="Stop A", lat=0.0, lon=0.0)
    G.add_node("B", name="Stop B", lat=0.1, lon=0.1)
    G.add_node("C", name="Stop C", lat=0.2, lon=0.2)
    G.add_node("D", name="Stop D", lat=0.3, lon=0.3)

    G.add_edge("A", "B", weight=5, route_id="R1")
    G.add_edge("B", "C", weight=3, route_id="R1")
    G.add_edge("A", "C", weight=15, route_id="R2")
    G.add_edge("C", "D", weight=2, route_id="transfer")

    return G


def test_find_shortest_path_success(simple_graph):
    planner = RoutePlanner(simple_graph)
    result = planner.find_shortest_path("A", "C")
    assert result is not None
    path, cost = result
    assert path == ["A", "B", "C"]
    assert cost == 8


def test_find_alternative_routes_with_mock(monkeypatch):
    G = nx.MultiDiGraph()
    G.add_edge("A", "B", weight=1)
    G.add_edge("B", "C", weight=1)

    planner = RoutePlanner(G)

    # Mock nx.shortest_simple_paths to return predefined paths
    def mock_paths(graph, source, target, weight):
        return [["A", "B", "C"], ["A", "C"]]

    monkeypatch.setattr(nx, "shortest_simple_paths", mock_paths)

    routes = planner.find_alternative_routes("A", "C", k=2)
    assert len(routes) == 2
    assert routes[0][0] == ["A", "B", "C"]
    assert isinstance(routes[0][1], (int, float))


def test_find_shortest_path_no_path(simple_graph):
    planner = RoutePlanner(simple_graph)
    simple_graph.remove_edge("C", "D")
    result = planner.find_shortest_path("D", "A")
    assert result is None


def test_find_shortest_path_node_not_found(simple_graph):
    planner = RoutePlanner(simple_graph)
    result = planner.find_shortest_path("X", "C")
    assert result is None


def test_get_path_details(simple_graph):
    planner = RoutePlanner(simple_graph)
    path = ["A", "B", "C"]
    details = planner.get_path_details(path)
    assert len(details) == 3
    assert details[0]["stop_id"] == "A"
    assert details[0]["route_to_next"] == "R1"
    assert details[1]["is_transfer"] is False


def test_find_shortest_path_generic_exception():
    class FakeGraph:
        def successors(self):
            return ["B"]  # minimal fake method

    planner = RoutePlanner(FakeGraph())

    result = planner.find_shortest_path("A", "B")
    assert result is None


def test_find_alternative_routes_error():
    G = nx.MultiDiGraph()
    planner = RoutePlanner(G)
    result = planner.find_alternative_routes("X", "Y")
    assert result == []


def test_get_nearby_stops(simple_graph):
    planner = RoutePlanner(simple_graph)
    nearby = planner.get_nearby_stops("A", max_distance=3)
    assert set(nearby) == {"B", "C", "D"}


def test_get_nearby_stops_error_handling():
    planner = RoutePlanner(nx.MultiDiGraph())  # empty graph

    result = planner.get_nearby_stops("UNKNOWN_STOP")

    assert result == []
