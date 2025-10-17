"""FastAPI application entry point."""

import pandas as pd
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import make_asgi_app
from loguru import logger

from src.config import get_settings
from src.graph.builder import TransportGraphBuilder
from src.graph.router import RoutePlanner
from . import routes
from .models import HealthResponse

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan events."""
    logger.info("Starting DiviaMobilités Transport Planner API")

    # Load or build graph
    try:
        graph_path = settings.processed_data_dir / "transport_graph.gml"

        if graph_path.exists():
            logger.info("Loading existing graph")
            builder = TransportGraphBuilder()
            graph = builder.load_graph(graph_path)
        else:
            logger.info("Building new graph")
            builder = TransportGraphBuilder()
            graph = builder.build_graph()
            builder.save_graph(graph_path)

        # Initialize route planner
        routes.route_planner = RoutePlanner(graph)
        logger.info("Route planner initialized")

        # Load stops and routes data
        routes.stops_df = pd.read_csv(settings.processed_data_dir / "stops.csv")
        routes.routes_df = pd.read_csv(settings.processed_data_dir / "routes.csv")
        logger.info("Loaded stops and routes data")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        routes.route_planner = None

    yield

    logger.info("Shutting down API")


app = FastAPI(
    title="DiviaMobilités Transport Planner",
    description="Route planning API for DiviaMobilités public transport network",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_path = Path(__file__).parent.parent / "web" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    logger.info(f"Mounted static files from {static_path}")

# Include API routes
app.include_router(routes.router)

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Serve the web UI."""
    html_path = Path(__file__).parent.parent / "web" / "static" / "index.html"

    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    # Fallback to API info page
    return HTMLResponse(
        content="""
    <!DOCTYPE html>
    <html>
        <head>
            <title>DiviaMobilités Transport Planner</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    line-height: 1.6;
                }
                h1 { color: #2563eb; }
                .card {
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }
                a {
                    color: #2563eb;
                    text-decoration: none;
                }
                a:hover { text-decoration: underline; }
                ul { list-style: none; padding: 0; }
                li { padding: 8px 0; }
            </style>
        </head>
        <body>
            <h1>🚌 DiviaMobilités Transport Planner API</h1>
            <p>Welcome to the route planning API for DiviaMobilités public transport network!</p>
            
            <div class="card">
                <h2>📚 Documentation</h2>
                <ul>
                    <li>📖 <a href="/docs">Interactive API Documentation (Swagger UI)</a></li>
                    <li>📋 <a href="/redoc">Alternative Documentation (ReDoc)</a></li>
                    <li>📊 <a href="/metrics">Prometheus Metrics</a></li>
                </ul>
            </div>
            
            <div class="card">
                <h2>🔗 Quick Links</h2>
                <ul>
                    <li>🏥 <a href="/health">Health Check</a></li>
                    <li>🚏 <a href="/api/v1/stops?limit=10">List Stops</a></li>
                    <li>🚌 <a href="/api/v1/routes">List Routes</a></li>
                </ul>
            </div>
        </body>
    </html>
    """
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    graph_loaded = routes.route_planner is not None

    num_nodes = 0
    num_edges = 0
    if graph_loaded and routes.route_planner:
        num_nodes = routes.route_planner.graph.number_of_nodes()
        num_edges = routes.route_planner.graph.number_of_edges()

    return HealthResponse(
        status="healthy" if graph_loaded else "degraded",
        environment=settings.environment,
        graph_loaded=graph_loaded,
        num_nodes=num_nodes,
        num_edges=num_edges,
    )
