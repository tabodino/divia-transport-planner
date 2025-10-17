import pytest
import pandas as pd
import networkx as nx
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch
from src.graph.builder import TransportGraphBuilder


@pytest.fixture
def builder():
    return TransportGraphBuilder()


@pytest.fixture
def sample_data():
    stops_df = pd.DataFrame(
        [
            {"stop_id": "A", "stop_name": "Stop A", "stop_lat": 0.0, "stop_lon": 0.0},
            {
                "stop_id": "B",
                "stop_name": "Stop B",
                "stop_lat": 0.001,
                "stop_lon": 0.001,
            },
            {"stop_id": "C", "stop_name": "Stop C", "stop_lat": 0.01, "stop_lon": 0.01},
        ]
    )

    routes_df = pd.DataFrame([{"route_id": "R1"}])

    trips_df = pd.DataFrame(
        [
            {"trip_id": "T1", "route_id": "R1"},
        ]
    )

    stop_times_df = pd.DataFrame(
        [
            {
                "trip_id": "T1",
                "stop_id": "A",
                "stop_sequence": 1,
                "arrival_time": "00:00:00",
            },
            {
                "trip_id": "T1",
                "stop_id": "B",
                "stop_sequence": 2,
                "arrival_time": "00:05:00",
            },
        ]
    )

    return stops_df, routes_df, trips_df, stop_times_df


def test_load_gtfs_data(builder, sample_data):
    stops, routes, trips, stop_times = sample_data

    with patch(
        "pandas.read_csv", side_effect=[stops, routes, trips, stop_times]
    ) as mock_csv:
        with patch("src.graph.builder.settings") as mock_settings:
            mock_settings.processed_data_dir = Path("mock_dir")
            builder.load_gtfs_data()

    assert builder.stops_df.equals(stops)
    assert builder.routes_df.equals(routes)
    assert builder.trips_df.equals(trips)
    assert builder.stop_times_df.equals(stop_times)
    assert mock_csv.call_count == 4


def test_add_stops_as_nodes(builder, sample_data):
    builder.stops_df, _, _, _ = sample_data
    builder.add_stops_as_nodes()

    assert builder.graph.number_of_nodes() == 3
    assert "A" in builder.graph.nodes
    assert builder.graph.nodes["A"]["name"] == "Stop A"


def test_add_route_connections(builder, sample_data):
    stops_df, routes_df, trips_df, stop_times_df = sample_data
    builder.stops_df = stops_df
    builder.routes_df = routes_df
    builder.trips_df = trips_df
    builder.stop_times_df = stop_times_df

    builder.add_stops_as_nodes()
    builder.add_route_connections()

    assert builder.graph.number_of_edges() == 1
    edge_data = list(builder.graph.edges(data=True))[0][2]
    assert edge_data["route_id"] == "R1"
    assert edge_data["trip_id"] == "T1"
    assert edge_data["weight"] > 0


def test_add_transfer_connections(builder, sample_data):
    builder.stops_df, _, _, _ = sample_data
    builder.add_stops_as_nodes()
    builder.add_transfer_connections(max_transfer_distance=0.005)

    edges = list(builder.graph.edges(data=True))
    assert any(e[2]["route_id"] == "transfer" for e in edges)


def test_add_route_connections_no_arrival_time(builder):
    builder.stops_df = pd.DataFrame(
        [
            {"stop_id": "A", "stop_name": "Stop A", "stop_lat": 0.0, "stop_lon": 0.0},
            {
                "stop_id": "B",
                "stop_name": "Stop B",
                "stop_lat": 0.001,
                "stop_lon": 0.001,
            },
        ]
    )
    builder.trips_df = pd.DataFrame([{"trip_id": "T1", "route_id": "R1"}])
    builder.stop_times_df = pd.DataFrame(
        [
            {"trip_id": "T1", "stop_id": "A", "stop_sequence": 1},
            {"trip_id": "T1", "stop_id": "B", "stop_sequence": 2},
        ]
    )
    builder.add_stops_as_nodes()
    builder.add_route_connections()

    # Check if edge exist with weight=1
    edge_data = list(builder.graph.edges(data=True))[0][2]
    assert edge_data["weight"] == 1


def test_parse_gtfs_time_valid(builder):
    td = builder.parse_gtfs_time("25:30:00")
    assert isinstance(td, timedelta)
    assert td.total_seconds() == 25 * 3600 + 30 * 60


def test_parse_gtfs_time_invalid(builder):
    assert builder.parse_gtfs_time("bad:time") is None


def test_build_graph_with_transfers(builder):
    with (
        patch.object(builder, "load_gtfs_data") as m_load,
        patch.object(builder, "add_stops_as_nodes") as m_nodes,
        patch.object(builder, "add_route_connections") as m_routes,
        patch.object(builder, "add_transfer_connections") as m_transfers,
    ):
        builder.build_graph(include_transfers=True)

        m_load.assert_called_once()
        m_nodes.assert_called_once()
        m_routes.assert_called_once()
        m_transfers.assert_called_once()


def test_build_graph_without_transfers(builder):
    with (
        patch.object(builder, "load_gtfs_data"),
        patch.object(builder, "add_stops_as_nodes"),
        patch.object(builder, "add_route_connections"),
        patch.object(builder, "add_transfer_connections") as m_transfers,
    ):
        builder.build_graph(include_transfers=False)
        m_transfers.assert_not_called()


def test_save_graph_default_path(builder):
    with (
        patch("networkx.write_gml") as mock_write,
        patch("src.graph.builder.settings") as mock_settings,
    ):
        mock_settings.processed_data_dir = Path("mock_dir")
        builder.graph.add_node("A")

        builder.save_graph()
        expected_path = Path("mock_dir") / "transport_graph.gml"
        mock_write.assert_called_once_with(builder.graph, expected_path)


def test_load_graph_default_path(builder):
    with (
        patch("networkx.read_gml", return_value=nx.MultiDiGraph()) as mock_read,
        patch("src.graph.builder.settings") as mock_settings,
    ):
        mock_settings.processed_data_dir = Path("mock_dir")

        graph = builder.load_graph()
        expected_path = Path("mock_dir") / "transport_graph.gml"
        mock_read.assert_called_once_with(expected_path)
        assert isinstance(graph, nx.MultiDiGraph)
