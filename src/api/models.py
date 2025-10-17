"""Pydantic models for API requests and responses."""

from typing import List, Optional
from pydantic import BaseModel, Field


class RouteRequest(BaseModel):
    """Request model for route planning."""

    departure: str = Field(..., description="Departure stop ID")
    arrival: str = Field(..., description="Arrival stop ID")
    alternatives: int = Field(1, ge=1, le=5, description="Number of alternative routes")


class StopInfo(BaseModel):
    """Information about a stop."""

    stop_id: str
    stop_name: str
    lat: float
    lon: float
    sequence: int
    route_to_next: Optional[str] = None
    is_transfer: Optional[bool] = None


class RouteResponse(BaseModel):
    """Response model for route planning."""

    origin: str
    destination: str
    path: List[str]
    stops: List[StopInfo]
    total_cost: float
    num_stops: int
    num_transfers: int


class AlternativeRoutesResponse(BaseModel):
    """Response model for alternative routes."""

    origin: str
    destination: str
    routes: List[RouteResponse]


class Stop(BaseModel):
    """Stop model."""

    stop_id: str
    stop_name: str
    lat: float
    lon: float


class StopsResponse(BaseModel):
    """Response model for stops list."""

    stops: List[Stop]
    total: int


class Route(BaseModel):
    """Route model."""

    route_id: str
    route_short_name: str
    route_long_name: str
    route_type: int


class RoutesResponse(BaseModel):
    """Response model for routes list."""

    routes: List[Route]
    total: int


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    environment: str
    graph_loaded: bool
    num_nodes: int
    num_edges: int
