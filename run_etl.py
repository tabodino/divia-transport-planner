"""Script to execute GTFS ETL."""

import sys
from pathlib import Path
from loguru import logger
from src.etl.load_gtfs import GTFSLoader
from src.config import get_settings

# Ensure the src directory is in the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    """Execute complete pipeline for the GTFS ETL."""
    settings = get_settings()

    logger.info("Starting ETL GTFS pipeline...")
    logger.info(f"URL GTFS: {settings.gtfs_url}")

    loader = GTFSLoader(gtfs_url=settings.gtfs_url)
    print(settings.gtfs_url)
    gtfs_data = loader.run_etl()

    logger.info("Pipeline ETL terminated with success!")
    logger.info(f"Processed files: {list(gtfs_data.keys())}")

    return gtfs_data


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        logger.error(f"Error during ETL execution: {e}")
        sys.exit(1)
