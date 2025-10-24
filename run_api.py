#!/usr/bin/env python
"""Script simple pour lancer l'API FastAPI."""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import uvicorn
from src.config import get_settings

settings = get_settings()


def main():
    """Lance le serveur FastAPI."""
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.log_level,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
