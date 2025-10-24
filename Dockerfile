FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    pipx \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY pyproject.toml ./
COPY entrypoint.py ./
COPY run_api.py ./  
COPY run_etl.py ./
COPY run_gradio.py ./ 
COPY run_graph.py ./ 
COPY src ./src

RUN mkdir -p ./data

# Install dependencies
RUN uv pip install --system -e .

# Expose ports
EXPOSE 8000 7860

# Default command
CMD ["python", "entrypoint.py"]
