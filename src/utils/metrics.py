"""Prometheus metrics for monitoring."""

from prometheus_client import Counter, Histogram, Gauge

# API Metrics
api_requests_total = Counter(
    "api_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "status"],
)

api_request_duration = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"],
)

# Route Planning Metrics
route_calculations_total = Counter(
    "route_calculations_total", "Total number of route calculations", ["status"]
)

route_calculation_duration = Histogram(
    "route_calculation_duration_seconds", "Route calculation duration in seconds"
)

# Graph Metrics
graph_nodes = Gauge("graph_nodes_total", "Total number of nodes in the transport graph")

graph_edges = Gauge("graph_edges_total", "Total number of edges in the transport graph")

# LLM Metrics
llm_requests_total = Counter(
    "llm_requests_total", "Total number of LLM requests", ["status"]
)

llm_request_duration = Histogram(
    "llm_request_duration_seconds", "LLM request duration in seconds"
)

llm_tokens_total = Counter("llm_tokens_total", "Total number of LLM tokens", ["type"])
