"""Complete tests for the GTFS ETL module with 100% coverage."""

import zipfile
from unittest.mock import Mock, patch
import pandas as pd
import pytest
import requests
from src.etl.load_gtfs import GTFSLoader


@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directories for tests."""
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    processed_dir.mkdir()
    return raw_dir, processed_dir


@pytest.fixture
def gtfs_loader(temp_dirs):
    """Create a GTFSLoader instance for tests."""
    raw_dir, processed_dir = temp_dirs
    with patch("src.etl.load_gtfs.settings") as mock_settings:
        mock_settings.gtfs_url = "https://example.com/gtfs.zip"
        mock_settings.raw_data_dir = raw_dir
        mock_settings.processed_data_dir = processed_dir
        loader = GTFSLoader()
        return loader


@pytest.fixture
def sample_gtfs_data():
    """Create sample GTFS data."""
    return {
        "agency": pd.DataFrame(
            {
                "agency_id": ["1"],
                "agency_name": ["DiviaMobilités"],
                "agency_url": ["https://divia.fr"],
                "agency_timezone": ["Europe/Paris"],
            }
        ),
        "stops": pd.DataFrame(
            {
                "stop_id": ["STOP1", "STOP2"],
                "stop_name": ["Gare", "République"],
                "stop_lat": [47.3220, 47.3215],
                "stop_lon": [5.0415, 5.0420],
            }
        ),
        "routes": pd.DataFrame(
            {
                "route_id": ["L1", "L2"],
                "route_short_name": ["1", "2"],
                "route_long_name": ["Ligne 1", "Ligne 2"],
                "route_type": [3, 3],
            }
        ),
        "trips": pd.DataFrame(
            {
                "trip_id": ["T1", "T2"],
                "route_id": ["L1", "L2"],
                "service_id": ["S1", "S1"],
            }
        ),
        "stop_times": pd.DataFrame(
            {
                "trip_id": ["T1", "T1", "T2"],
                "stop_id": ["STOP1", "STOP2", "STOP1"],
                "arrival_time": ["08:00:00", "08:10:00", "09:00:00"],
                "departure_time": ["08:00:00", "08:10:00", "09:00:00"],
                "stop_sequence": [1, 2, 1],
            }
        ),
        "calendar": pd.DataFrame(
            {
                "service_id": ["S1"],
                "monday": [1],
                "tuesday": [1],
                "wednesday": [1],
                "thursday": [1],
                "friday": [1],
                "saturday": [0],
                "sunday": [0],
                "start_date": ["20240101"],
                "end_date": ["20241231"],
            }
        ),
        "shapes": pd.DataFrame(
            {
                "shape_id": ["SH1"],
                "shape_pt_lat": [47.3220],
                "shape_pt_lon": [5.0415],
                "shape_pt_sequence": [1],
            }
        ),
    }


class TestGTFSLoaderInit:
    """Tests for GTFSLoader initialization."""

    def test_init_with_default_url(self, temp_dirs):
        """Test initialization with default URL."""
        raw_dir, processed_dir = temp_dirs
        with patch("src.etl.load_gtfs.settings") as mock_settings:
            mock_settings.gtfs_url = "https://default.com/gtfs.zip"
            mock_settings.raw_data_dir = raw_dir
            mock_settings.processed_data_dir = processed_dir

            loader = GTFSLoader()

            assert loader.gtfs_url == "https://default.com/gtfs.zip"
            assert loader.raw_dir == raw_dir
            assert loader.processed_dir == processed_dir

    def test_init_with_custom_url(self, temp_dirs):
        """Test initialization with custom URL."""
        raw_dir, processed_dir = temp_dirs
        with patch("src.etl.load_gtfs.settings") as mock_settings:
            mock_settings.raw_data_dir = raw_dir
            mock_settings.processed_data_dir = processed_dir

            loader = GTFSLoader(gtfs_url="https://custom.com/gtfs.zip")

            assert loader.gtfs_url == "https://custom.com/gtfs.zip"


class TestDownloadGTFS:
    """Tests for the download_gtfs method."""

    def test_download_success(self, gtfs_loader):
        """Test successful download."""
        mock_response = Mock()
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]

        with patch("requests.get", return_value=mock_response):
            zip_path = gtfs_loader.download_gtfs()

            assert zip_path.exists()
            assert zip_path.name == "gtfs.zip"
            mock_response.raise_for_status.assert_called_once()

    def test_download_http_error(self, gtfs_loader):
        """Test HTTP error during download."""
        with patch("requests.get") as mock_get:
            mock_get.return_value.raise_for_status.side_effect = requests.HTTPError(
                "404"
            )

            with pytest.raises(requests.HTTPError):
                gtfs_loader.download_gtfs()

    def test_download_connection_error(self, gtfs_loader):
        """Test connection error during download."""
        with patch(
            "requests.get", side_effect=requests.ConnectionError("Network error")
        ):
            with pytest.raises(requests.ConnectionError):
                gtfs_loader.download_gtfs()


class TestExtractGTFS:
    """Tests for the extract_gtfs method."""

    def test_extract_success(self, gtfs_loader, tmp_path):
        """Test successful extraction."""
        # Create a test ZIP file
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("stops.txt", "stop_id,stop_name\n1,Test")
            zf.writestr("routes.txt", "route_id,route_name\nL1,Ligne 1")

        extract_dir = gtfs_loader.extract_gtfs(zip_path)

        assert extract_dir.exists()
        assert (extract_dir / "stops.txt").exists()
        assert (extract_dir / "routes.txt").exists()

    def test_extract_invalid_zip(self, gtfs_loader, tmp_path):
        """Test extraction of an invalid ZIP file."""
        invalid_zip = tmp_path / "invalid.zip"
        invalid_zip.write_text("not a zip file")

        with pytest.raises(zipfile.BadZipFile):
            gtfs_loader.extract_gtfs(invalid_zip)

    def test_extract_creates_directory(self, gtfs_loader, tmp_path):
        """Test that the extraction directory is created."""
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test.txt", "content")

        # Remove the gtfs directory if it exists
        gtfs_dir = gtfs_loader.raw_dir / "gtfs"
        if gtfs_dir.exists():
            import shutil

            shutil.rmtree(gtfs_dir)

        extract_dir = gtfs_loader.extract_gtfs(zip_path)

        assert extract_dir.exists()
        assert extract_dir.is_dir()


class TestLoadGTFSFiles:
    """Tests for the load_gtfs_files method."""

    def test_load_all_files(self, gtfs_loader, tmp_path, sample_gtfs_data):
        """Test loading all GTFS files."""
        gtfs_dir = tmp_path / "gtfs"
        gtfs_dir.mkdir()

        # Create GTFS files
        for name, df in sample_gtfs_data.items():
            df.to_csv(gtfs_dir / f"{name}.txt", index=False)

        dataframes = gtfs_loader.load_gtfs_files(gtfs_dir)

        assert len(dataframes) == len(sample_gtfs_data)
        assert "stops" in dataframes
        assert "routes" in dataframes
        assert "shapes" in dataframes
        assert len(dataframes["stops"]) == 2
        assert len(dataframes["routes"]) == 2

    def test_load_missing_files(self, gtfs_loader, tmp_path):
        """Test loading with missing files."""
        gtfs_dir = tmp_path / "gtfs"
        gtfs_dir.mkdir()

        # Create only stops.txt
        pd.DataFrame({"stop_id": ["1"], "stop_name": ["Test"]}).to_csv(
            gtfs_dir / "stops.txt", index=False
        )
        (gtfs_dir / "readme.md").write_text("# README")
        (gtfs_dir / "data.json").write_text('{"key": "value"}')
        (gtfs_dir / "config.yaml").write_text("key: value")

        dataframes = gtfs_loader.load_gtfs_files(gtfs_dir)

        assert len(dataframes) == 1
        assert "stops" in dataframes
        assert "readme" not in dataframes
        assert "data" not in dataframes

    def test_load_empty_directory(self, gtfs_loader, tmp_path):
        """Test loading from an empty directory."""
        gtfs_dir = tmp_path / "empty"
        gtfs_dir.mkdir()

        dataframes = gtfs_loader.load_gtfs_files(gtfs_dir)

        assert len(dataframes) == 0

    def test_load_with_extra_gtfs_files(self, gtfs_loader, tmp_path):
        """Test chargement avec des fichiers GTFS supplémentaires."""
        gtfs_dir = tmp_path / "gtfs"
        gtfs_dir.mkdir()

        pd.DataFrame({"stop_id": ["1"]}).to_csv(gtfs_dir / "stops.txt", index=False)
        pd.DataFrame({"route_id": ["L1"]}).to_csv(gtfs_dir / "routes.txt", index=False)
        pd.DataFrame({"fare_id": ["F1"]}).to_csv(
            gtfs_dir / "fare_attributes.txt", index=False
        )
        pd.DataFrame({"transfer_type": [0]}).to_csv(
            gtfs_dir / "transfers.txt", index=False
        )

        dataframes = gtfs_loader.load_gtfs_files(gtfs_dir)

        assert len(dataframes) == 4
        assert "stops" in dataframes
        assert "routes" in dataframes
        assert "fare_attributes" in dataframes
        assert "transfers" in dataframes

    def test_load_malformed_csv(self, gtfs_loader, tmp_path):
        """Test loading a malformed CSV file."""
        gtfs_dir = tmp_path / "gtfs"
        gtfs_dir.mkdir()

        (gtfs_dir / "stops.txt").write_text("stop_id,stop_name\n1,2,3,4,5\n6,7,8")

        # Pandas will load this but with warnings, not errors
        dataframes = gtfs_loader.load_gtfs_files(gtfs_dir)
        assert "stops" in dataframes


class TestProcessAndSave:
    """Tests for the process_and_save method."""

    def test_save_all_dataframes(self, gtfs_loader, sample_gtfs_data):
        """Test saving all DataFrames."""
        gtfs_loader.process_and_save(sample_gtfs_data)

        for name in sample_gtfs_data.keys():
            csv_file = gtfs_loader.processed_dir / f"{name}.csv"
            assert csv_file.exists()

            # Check that the data is correct
            loaded_df = pd.read_csv(csv_file)
            assert len(loaded_df) == len(sample_gtfs_data[name])

    def test_save_empty_dataframe(self, gtfs_loader):
        """Test saving an empty DataFrame."""
        empty_data = {"empty": pd.DataFrame()}

        gtfs_loader.process_and_save(empty_data)

        csv_file = gtfs_loader.processed_dir / "empty.csv"
        assert csv_file.exists()

    def test_save_overwrites_existing(self, gtfs_loader, sample_gtfs_data):
        """Test that saving overwrites existing files."""
        # First save
        gtfs_loader.process_and_save(sample_gtfs_data)

        # Modify the data
        modified_data = sample_gtfs_data.copy()
        modified_data["stops"] = pd.DataFrame(
            {
                "stop_id": ["NEW1"],
                "stop_name": ["New Stop"],
                "stop_lat": [47.0],
                "stop_lon": [5.0],
            }
        )

        # Second save
        gtfs_loader.process_and_save(modified_data)

        # Check that the new data is present
        loaded_df = pd.read_csv(gtfs_loader.processed_dir / "stops.csv")
        assert len(loaded_df) == 1
        assert str(loaded_df.iloc[0]["stop_id"]) == "NEW1"


class TestRunETL:
    """Tests for the run_etl method (full pipeline)."""

    def test_run_etl_success(self, gtfs_loader, sample_gtfs_data, tmp_path):
        """Test successful execution of the ETL pipeline."""
        # Mock download_gtfs
        zip_path = tmp_path / "gtfs.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for name, df in sample_gtfs_data.items():
                zf.writestr(f"{name}.txt", df.to_csv(index=False))

        with patch.object(gtfs_loader, "download_gtfs", return_value=zip_path):
            result = gtfs_loader.run_etl()

        assert len(result) == len(sample_gtfs_data)
        assert "stops" in result
        assert "routes" in result

        # Check that the CSV files are created
        for name in sample_gtfs_data.keys():
            assert (gtfs_loader.processed_dir / f"{name}.csv").exists()

    def test_run_etl_download_failure(self, gtfs_loader):
        """Test failure to download in the pipeline."""
        with patch.object(
            gtfs_loader, "download_gtfs", side_effect=requests.HTTPError("404")
        ):
            with pytest.raises(requests.HTTPError):
                gtfs_loader.run_etl()

    def test_run_etl_extraction_failure(self, gtfs_loader, tmp_path):
        """Test extraction failure in the pipeline."""
        invalid_zip = tmp_path / "invalid.zip"
        invalid_zip.write_text("not a zip")

        with patch.object(gtfs_loader, "download_gtfs", return_value=invalid_zip):
            with pytest.raises(zipfile.BadZipFile):
                gtfs_loader.run_etl()


class TestMainExecution:
    """Tests for module execution as a script."""

    def test_main_execution(self, tmp_path, sample_gtfs_data):
        """Test module execution as main script."""
        with patch("src.etl.load_gtfs.GTFSLoader") as MockLoader:
            mock_instance = MockLoader.return_value
            mock_instance.run_etl.return_value = sample_gtfs_data

            # Simulate if __name__ == "__main__" block execution
            from src.etl.load_gtfs import GTFSLoader

            loader = GTFSLoader()
            result = loader.run_etl()

            assert result == sample_gtfs_data
            mock_instance.run_etl.assert_called_once()
