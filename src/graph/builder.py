"""Build NetworkX graph from GTFS data."""

from pathlib import Path
from datetime import timedelta
import networkx as nx
import pandas as pd
from loguru import logger
from src.config import get_settings
from src.utils.metrics import graph_nodes, graph_edges


settings = get_settings()


class TransportGraphBuilder:
    """Build and manage transport network graph."""

    def __init__(self):
        """Initialize graph builder."""
        self.graph = nx.MultiDiGraph()
        self.stops_df: pd.DataFrame | None = None
        self.routes_df: pd.DataFrame | None = None
        self.trips_df: pd.DataFrame | None = None
        self.stop_times_df: pd.DataFrame | None = None

    def load_gtfs_data(self) -> None:
        """Load processed GTFS data."""
        logger.info("Loading GTFS data for graph construction")

        data_dir = settings.processed_data_dir

        self.stops_df = pd.read_csv(data_dir / "stops.csv")
        self.routes_df = pd.read_csv(data_dir / "routes.csv")
        self.trips_df = pd.read_csv(data_dir / "trips.csv")
        self.stop_times_df = pd.read_csv(data_dir / "stop_times.csv")

        logger.info(f"Loaded {len(self.stops_df)} stops, {len(self.routes_df)} routes")

    def add_stops_as_nodes(self) -> None:
        """Add all stops as nodes in the graph."""
        logger.info("Adding stops as nodes")

        for _, stop in self.stops_df.iterrows():
            self.graph.add_node(
                stop["stop_id"],
                name=stop["stop_name"],
                lat=stop["stop_lat"],
                lon=stop["stop_lon"],
            )

        graph_nodes.set(self.graph.number_of_nodes())
        logger.info(f"Added {self.graph.number_of_nodes()} nodes")

    def add_route_connections(self) -> None:
        """Add edges based on stop sequences in trips."""
        logger.info("Adding route connections as edges")

        # Merge trips with stop_times to get route info
        stop_times_with_routes = self.stop_times_df.merge(
            self.trips_df[["trip_id", "route_id"]], on="trip_id"
        )

        # Sort by trip and stop sequence
        stop_times_with_routes = stop_times_with_routes.sort_values(
            ["trip_id", "stop_sequence"]
        )

        # Create edges for consecutive stops in each trip
        edges_added = 0
        for trip_id, group in stop_times_with_routes.groupby("trip_id"):
            stops = group["stop_id"].tolist()
            route_id = group["route_id"].iloc[0]

            for i in range(len(stops) - 1):
                from_stop = stops[i]
                to_stop = stops[i + 1]

                # Calculate travel time if available
                if "arrival_time" in group.columns:
                    from_time_str = group.iloc[i]["arrival_time"]
                    to_time_str = group.iloc[i + 1]["arrival_time"]

                    from_time = self.parse_gtfs_time(from_time_str)
                    to_time = self.parse_gtfs_time(to_time_str)

                    if from_time is not None and to_time is not None:
                        duration = (to_time - from_time).total_seconds()
                        # Avoid negative or zero durations
                        if duration > 0:
                            weight = duration
                else:
                    weight = 1

                self.graph.add_edge(
                    from_stop,
                    to_stop,
                    route_id=route_id,
                    trip_id=trip_id,
                    weight=weight,
                )
                edges_added += 1

        graph_edges.set(self.graph.number_of_edges())
        logger.info(f"Added {edges_added} edges")

    def add_transfer_connections(self, max_transfer_distance: float = 0.005) -> None:
        """Add walking transfer connections between nearby stops.

        Args:
            max_transfer_distance: Maximum distance for transfers (in degrees, ~500m)
        """
        logger.info("Adding transfer connections")

        transfer_weight = 5  # Penalty for transfers
        transfers_added = 0

        # For each stop, find nearby stops
        for _, stop in self.stops_df.iterrows():
            stop_id = stop["stop_id"]
            lat, lon = stop["stop_lat"], stop["stop_lon"]

            # Find stops within transfer distance
            nearby = self.stops_df[
                (abs(self.stops_df["stop_lat"] - lat) < max_transfer_distance)
                & (abs(self.stops_df["stop_lon"] - lon) < max_transfer_distance)
                & (self.stops_df["stop_id"] != stop_id)
            ]

            for _, nearby_stop in nearby.iterrows():
                self.graph.add_edge(
                    stop_id,
                    nearby_stop["stop_id"],
                    route_id="transfer",
                    weight=transfer_weight,
                )
                transfers_added += 1

        logger.info(f"Added {transfers_added} transfer connections")

    # We use MultiDiGraph to allow multiple edges between nodes
    def build_graph(self, include_transfers: bool = True) -> nx.MultiDiGraph:
        """Build complete transport graph.

        Args:
            include_transfers: Whether to add walking transfer connections

        Returns:
            Complete transport network graph
        """
        logger.info("Building transport network graph")

        self.load_gtfs_data()
        self.add_stops_as_nodes()
        self.add_route_connections()

        if include_transfers:
            self.add_transfer_connections()

        logger.info(
            f"Graph built: {self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges"
        )

        return self.graph

    def save_graph(self, filepath: Path | None = None) -> None:
        """Save graph to file.

        Args:
            filepath: Path to save graph (default: processed_data_dir/transport_graph.gml)
        """
        if filepath is None:
            filepath = settings.processed_data_dir / "transport_graph.gml"

        nx.write_gml(self.graph, filepath)
        logger.info(f"Graph saved to {filepath}")

    def load_graph(self, filepath: Path | None = None) -> nx.MultiDiGraph:
        """Load graph from file.

        Args:
            filepath: Path to load graph from

        Returns:
            Loaded graph
        """
        if filepath is None:
            filepath = settings.processed_data_dir / "transport_graph.gml"

        self.graph = nx.read_gml(filepath)
        graph_nodes.set(self.graph.number_of_nodes())
        graph_edges.set(self.graph.number_of_edges())
        logger.info(f"Graph loaded from {filepath}")

        return self.graph

    def parse_gtfs_time(self, time_str: str) -> timedelta | None:
        """Convert GTFS time string (can exceed 24h) to timedelta."""
        try:
            hours, minutes, seconds = map(int, time_str.split(":"))
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
        except Exception:
            return None


if __name__ == "__main__":  # pragma: no cover
    builder = TransportGraphBuilder()
    graph = builder.build_graph()
    builder.save_graph()
