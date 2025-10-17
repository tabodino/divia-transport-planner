"""Route planning algorithms using NetworkX."""

from typing import List, Dict, Any, Tuple
import networkx as nx
from loguru import logger
from src.utils.metrics import route_calculations_total, route_calculation_duration


class RoutePlanner:
    """Plan routes using NetworkX shortest path algorithms."""

    def __init__(self, graph: nx.MultiDiGraph):
        """Initialize route planner.

        Args:
            graph: Transport network graph
        """
        self.graph = graph

    def find_shortest_path(
        self, origin: str, destination: str, weight: str = "weight"
    ) -> Tuple[List[str], float] | None:
        """Find shortest path between two stops.

        Args:
            origin: Origin stop ID
            destination: Destination stop ID
            weight: Edge attribute to use as weight

        Returns:
            Tuple of (path as list of stop IDs, total cost) or None if no path exists
        """
        try:
            with route_calculation_duration.time():
                # Find shortest path
                path = nx.shortest_path(
                    self.graph, source=origin, target=destination, weight=weight
                )

                # Calculate total cost
                total_cost = 0
                for i in range(len(path) - 1):
                    # Get edge data (may have multiple edges)
                    edges = self.graph.get_edge_data(path[i], path[i + 1])
                    if edges:
                        # Use the first edge's weight
                        edge_data = list(edges.values())[0]
                        total_cost += edge_data.get(weight, 1)

            route_calculations_total.labels(status="success").inc()
            logger.info(f"Found path from {origin} to {destination}: {len(path)} stops")
            return path, total_cost

        except nx.NetworkXNoPath:
            route_calculations_total.labels(status="no_path").inc()
            logger.warning(f"No path found from {origin} to {destination}")
            return None
        except nx.NodeNotFound as e:
            route_calculations_total.labels(status="error").inc()
            logger.error(f"Stop not found: {e}")
            return None
        except Exception as e:
            route_calculations_total.labels(status="error").inc()
            logger.error(f"Error finding path: {e}")
            return None

    def get_path_details(self, path: List[str]) -> List[Dict[str, Any]]:
        """Get detailed information about a path.

        Args:
            path: List of stop IDs

        Returns:
            List of dictionaries with stop and route information
        """
        details = []

        for i, stop_id in enumerate(path):
            stop_info = {
                "stop_id": stop_id,
                "stop_name": self.graph.nodes[stop_id].get("name", "Unknown"),
                "lat": self.graph.nodes[stop_id].get("lat"),
                "lon": self.graph.nodes[stop_id].get("lon"),
                "sequence": i,
            }

            # Add route info for the edge to next stop
            if i < len(path) - 1:
                next_stop = path[i + 1]
                edges = self.graph.get_edge_data(stop_id, next_stop)
                if edges:
                    edge_data = list(edges.values())[0]
                    stop_info["route_to_next"] = edge_data.get("route_id")
                    stop_info["is_transfer"] = edge_data.get("route_id") == "transfer"

            details.append(stop_info)

        return details

    def find_alternative_routes(
        self, origin: str, destination: str, k: int = 3
    ) -> List[Tuple[List[str], float]]:
        """Find k shortest paths between two stops.

        Args:
            origin: Origin stop ID
            destination: Destination stop ID
            k: Number of alternative routes to find

        Returns:
            List of (path, cost) tuples
        """
        try:
            paths = list(
                nx.shortest_simple_paths(
                    self.graph, source=origin, target=destination, weight="weight"
                )
            )

            results = []
            for path in paths[:k]:
                # Calculate cost
                total_cost = 0
                for i in range(len(path) - 1):
                    edges = self.graph.get_edge_data(path[i], path[i + 1])
                    if edges:
                        edge_data = list(edges.values())[0]
                        total_cost += edge_data.get("weight", 1)
                results.append((path, total_cost))

            logger.info(f"Found {len(results)} alternative routes")
            return results

        except Exception as e:
            logger.error(f"Error finding alternative routes: {e}")
            return []

    def get_nearby_stops(self, stop_id: str, max_distance: int = 3) -> List[str]:
        """Get stops within a certain distance.

        Args:
            stop_id: Stop ID
            max_distance: Maximum number of hops

        Returns:
            List of nearby stop IDs
        """
        try:
            # Use Breadth First Search (BFS) to find stops within max_distance hops
            nearby = []
            visited = {stop_id}
            queue = [(stop_id, 0)]

            while queue:
                current, distance = queue.pop(0)

                if distance < max_distance:
                    for neighbor in self.graph.successors(current):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            nearby.append(neighbor)
                            queue.append((neighbor, distance + 1))

            return nearby

        except Exception as e:
            logger.error(f"Error finding nearby stops: {e}")
            return []
