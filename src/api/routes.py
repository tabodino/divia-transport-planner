"""API routes for route planning."""

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
import pandas as pd

from .models import (
    RouteRequest,
    RouteResponse,
    AlternativeRoutesResponse,
    StopsResponse,
    RoutesResponse,
    Stop,
    Route,
    StopInfo,
)
from ..graph.router import RoutePlanner
from ..config import get_settings
from ..utils.metrics import api_requests_total, api_request_duration

router = APIRouter(prefix="/api/v1", tags=["routing"])
settings = get_settings()

# Global variables for graph and planner (loaded at startup)
route_planner: RoutePlanner | None = None
stops_df: pd.DataFrame | None = None
routes_df: pd.DataFrame | None = None


def get_planner() -> RoutePlanner:
    """Get route planner instance."""
    if route_planner is None:
        raise HTTPException(status_code=503, detail="Route planner not initialized")
    return route_planner


@router.post("/route", response_model=RouteResponse | AlternativeRoutesResponse)
async def calculate_route(
    request: RouteRequest,
) -> RouteResponse | AlternativeRoutesResponse:
    """
    Calculate route between two stops.

    By default, returns only the shortest path for fast response.
    Set include_alternatives=true to get multiple route options (slower).
    """
    with api_request_duration.labels(method="POST", endpoint="/route").time():
        planner = get_planner()

        if request.include_alternatives:
            # Calculate multiple alternative routes (slower)
            logger.info(
                f"Calculating {request.max_alternatives} alternative routes "
                f"from {request.departure} to {request.arrival}"
            )

            results = planner.find_alternative_routes(
                request.departure, request.arrival, k=request.max_alternatives
            )

            if not results:
                api_requests_total.labels(
                    method="POST", endpoint="/route", status="404"
                ).inc()
                raise HTTPException(
                    status_code=404,
                    detail=f"No routes found from {request.departure} to {request.arrival}",
                )

            routes = []
            for path, total_cost in results:
                stops = planner.get_path_details(path)
                num_transfers = sum(
                    1 for stop in stops if stop.get("is_transfer", False)
                )

                routes.append(
                    RouteResponse(
                        origin=request.departure,
                        destination=request.arrival,
                        path=path,
                        stops=[StopInfo(**stop) for stop in stops],
                        total_cost=total_cost,
                        num_stops=len(path),
                        num_transfers=num_transfers,
                    )
                )

            api_requests_total.labels(
                method="POST", endpoint="/route", status="200"
            ).inc()

            return AlternativeRoutesResponse(
                origin=request.departure,
                destination=request.arrival,
                routes=routes,
            )
        else:
            # Calculate only shortest path (fast)
            logger.info(
                f"Calculating shortest route from {request.departure} to {request.arrival}"
            )

            result = planner.find_shortest_path(request.departure, request.arrival)

            if result is None:
                api_requests_total.labels(
                    method="POST", endpoint="/route", status="404"
                ).inc()
                raise HTTPException(
                    status_code=404,
                    detail=f"No route found from {request.departure} to {request.arrival}",
                )

            path, total_cost = result
            stops = planner.get_path_details(path)

            # Count transfers
            num_transfers = sum(1 for stop in stops if stop.get("is_transfer", False))

            api_requests_total.labels(
                method="POST", endpoint="/route", status="200"
            ).inc()

            return RouteResponse(
                origin=request.departure,
                destination=request.arrival,
                path=path,
                stops=[StopInfo(**stop) for stop in stops],
                total_cost=total_cost,
                num_stops=len(path),
                num_transfers=num_transfers,
            )


@router.post(
    "/route/alternatives", response_model=AlternativeRoutesResponse, deprecated=True
)
async def calculate_alternative_routes(
    request: RouteRequest,
) -> AlternativeRoutesResponse:
    """
    Calculate alternative routes between two stops.

    DEPRECATED: Use POST /route with include_alternatives=true instead.
    """
    # Force alternatives calculation
    request.include_alternatives = True
    return await calculate_route(request)


@router.get("/stops", response_model=StopsResponse)
async def get_stops(
    search: str = Query(None, description="Search stops by name"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of stops to return"
    ),
) -> StopsResponse:
    """Get list of all stops."""
    with api_request_duration.labels(method="GET", endpoint="/stops").time():
        if stops_df is None:
            api_requests_total.labels(
                method="GET", endpoint="/stops", status="503"
            ).inc()
            raise HTTPException(status_code=503, detail="Stops data not loaded")

        df = stops_df.copy()

        # Filter by search term
        if search:
            df = df[df["stop_name"].str.contains(search, case=False, na=False)]

        # Limit results
        df = df.head(limit)

        stops = [
            Stop(
                stop_id=row["stop_id"],
                stop_name=row["stop_name"],
                lat=row["stop_lat"],
                lon=row["stop_lon"],
            )
            for _, row in df.iterrows()
        ]

        api_requests_total.labels(method="GET", endpoint="/stops", status="200").inc()

        return StopsResponse(stops=stops, total=len(stops_df))


@router.get("/routes", response_model=RoutesResponse)
async def get_routes() -> RoutesResponse:
    """Get list of all routes."""
    with api_request_duration.labels(method="GET", endpoint="/routes").time():
        if routes_df is None:
            api_requests_total.labels(
                method="GET", endpoint="/routes", status="503"
            ).inc()
            raise HTTPException(status_code=503, detail="Routes data not loaded")

        routes = [
            Route(
                route_id=row["route_id"],
                route_short_name=row.get("route_short_name", ""),
                route_long_name=row.get("route_long_name", ""),
                route_type=row.get("route_type", 3),
            )
            for _, row in routes_df.iterrows()
        ]

        api_requests_total.labels(method="GET", endpoint="/routes", status="200").inc()

        return RoutesResponse(routes=routes, total=len(routes_df))


@router.get("/stops/{stop_id}/nearby")
async def get_nearby_stops(
    stop_id: str,
    max_distance: int = Query(3, ge=1, le=10, description="Maximum distance in hops"),
) -> StopsResponse:
    """Get nearby stops within a certain distance."""
    with api_request_duration.labels(method="GET", endpoint="/stops/nearby").time():
        planner = get_planner()

        if stops_df is None:
            api_requests_total.labels(
                method="GET", endpoint="/stops/nearby", status="503"
            ).inc()
            raise HTTPException(status_code=503, detail="Stops data not loaded")

        nearby_ids = planner.get_nearby_stops(stop_id, max_distance)

        nearby_stops = stops_df[stops_df["stop_id"].isin(nearby_ids)]

        stops = [
            Stop(
                stop_id=row["stop_id"],
                stop_name=row["stop_name"],
                lat=row["stop_lat"],
                lon=row["stop_lon"],
            )
            for _, row in nearby_stops.iterrows()
        ]

        api_requests_total.labels(
            method="GET", endpoint="/stops/nearby", status="200"
        ).inc()

        return StopsResponse(stops=stops, total=len(stops))
