"""Load and process GTFS data from DiviaMobilités."""

import zipfile
from pathlib import Path
from typing import Dict

import pandas as pd
import requests
from loguru import logger

from src.config import get_settings


settings = get_settings()


class GTFSLoader:
    """Load and process GTFS data."""

    def __init__(self, gtfs_url: str | None = None):
        """Initialize GTFS loader.

        Args:
            gtfs_url: URL to download GTFS data from
        """
        self.gtfs_url = gtfs_url or settings.gtfs_url
        self.raw_dir = settings.raw_data_dir
        self.processed_dir = settings.processed_data_dir

    def download_gtfs(self) -> Path:
        """Download GTFS zip file.

        Returns:
            Path to downloaded zip file
        """
        logger.info(f"Downloading GTFS data from {self.gtfs_url}")

        response = requests.get(self.gtfs_url, stream=True, timeout=30)
        response.raise_for_status()

        zip_path = self.raw_dir / "gtfs.zip"
        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Downloaded GTFS data to {zip_path}")
        return zip_path

    def extract_gtfs(self, zip_path: Path) -> Path:
        """Extract GTFS zip file.

        Args:
            zip_path: Path to GTFS zip file

        Returns:
            Path to extracted directory
        """
        extract_dir = self.raw_dir / "gtfs"
        extract_dir.mkdir(exist_ok=True)

        logger.info(f"Extracting GTFS data to {extract_dir}")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        logger.info("GTFS data extracted successfully")
        return extract_dir

    def load_gtfs_files(self, gtfs_dir: Path) -> Dict[str, pd.DataFrame]:
        """Load GTFS text files into pandas DataFrames.

        Args:
            gtfs_dir: Directory containing GTFS files

        Returns:
            Dictionary of DataFrames for each GTFS file
        """
        logger.info("Loading GTFS files into DataFrames")

        gtfs_files = [
            "agency.txt",
            "stops.txt",
            "routes.txt",
            "trips.txt",
            "stop_times.txt",
            "calendar.txt",
            "shapes.txt",
        ]

        dataframes = {}
        for filename in gtfs_files:
            file_path = gtfs_dir / filename
            if file_path.exists():
                logger.info(f"Loading {filename}")
                dataframes[filename.replace(".txt", "")] = pd.read_csv(file_path)
            else:
                logger.warning(f"File {filename} not found")

        logger.info(f"Loaded {len(dataframes)} GTFS files")
        return dataframes

    def process_and_save(self, dataframes: Dict[str, pd.DataFrame]) -> None:
        """Process and save GTFS data.

        Args:
            dataframes: Dictionary of GTFS DataFrames
        """
        logger.info("Processing and saving GTFS data")

        for name, df in dataframes.items():
            output_path = self.processed_dir / f"{name}.csv"
            df.to_csv(output_path, index=False)
            logger.info(f"Saved {name} to {output_path}")

    def run_etl(self) -> Dict[str, pd.DataFrame]:
        """Run complete ETL pipeline.

        Returns:
            Dictionary of processed DataFrames
        """
        logger.info("Starting GTFS ETL pipeline")

        # Download and extract
        zip_path = self.download_gtfs()
        gtfs_dir = self.extract_gtfs(zip_path)

        # Load data
        dataframes = self.load_gtfs_files(gtfs_dir)

        # Process and save
        self.process_and_save(dataframes)

        logger.info("GTFS ETL pipeline completed successfully")
        return dataframes


if __name__ == "__main__":  # pragma: no cover
    loader = GTFSLoader()
    loader.run_etl()
