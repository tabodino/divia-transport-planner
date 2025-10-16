.PHONY: test test-cov test-watch lint format

test:
	uv run pytest tests/ -v

test-cov:
	@echo "Test execution with coverage report"
	uv run pytest --cov=src --cov-report=html tests/


lint:
	@echo "Running linter (ruff)..."
	uv run ruff check src/ tests/

format:
	@echo "Formatting code with linter (ruff)..."
	uv run ruff format src/ tests/


etl:
	uv run python run_etl.py

build-graph:
	uv run python run_graph.py

notebook:
	uv run jupyter notebook notebooks/


help:
	@echo "Available commands:"
	@echo "Execution:"
	@echo "  make etl          - Download and extract GTFS data"
	@echo "  make build-graph  - Build the transport graph with networkX"
	@echo "  make notebook     - Open Jupyter Notebook"
	@echo ""
	@echo "Tests:"
	@echo "  make test         - Run tests"
	@echo "  make test-cov     - Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         - Lint the code with ruff"
	@echo "  make format       - Format the code with ruff"