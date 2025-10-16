#!/usr/bin/env python
"""Script to build and save the transport graph."""

from src.graph.builder import TransportGraphBuilder
from src.config import get_settings
from loguru import logger

settings = get_settings()


def main():
    """Build and save transport graph."""
    logger.info("Building transport graph from GTFS data")

    builder = TransportGraphBuilder()
    graph = builder.build_graph(include_transfers=True)

    # Save graph
    graph_path = settings.processed_data_dir / "transport_graph.gml"
    builder.save_graph(graph_path)

    logger.info(f"Graph saved to {graph_path}")
    logger.info(f"Nodes: {graph.number_of_nodes()}")
    logger.info(f"Edges: {graph.number_of_edges()}")


if __name__ == "__main__":
    main()
