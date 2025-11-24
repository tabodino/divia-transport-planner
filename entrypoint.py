import os
import sys
import subprocess
from pathlib import Path

REQUIRED_FILES = ["data/processed/stops.csv", "data/processed/routes.csv"]
DEFAULT_APP_MODE = "api"
API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = os.environ.get("API_PORT", "8000")
API_CMD = [
    "uvicorn",
    "src.api.main:final_app",
    "--host",
    API_HOST,
    "--port",
    API_PORT,
]


def data_ready():
    """Checks if all required processed data files exist."""
    return all(Path(f).exists() for f in REQUIRED_FILES)


def main():
    # 1. Check presence of processed data, run ETL if missing
    if not data_ready():
        print("\n Processed data not found! Running ETL routine to prepare data…")
        try:
            subprocess.run([sys.executable, "run_etl.py"], check=True)
        except subprocess.CalledProcessError:
            print("ETL failed, cannot continue.")
            exit(1)
        print("Data processing complete.")

    else:
        print("All required processed data files are present.")

    # 2. Start the selected application mode
    app_mode = os.environ.get("APP_MODE", DEFAULT_APP_MODE).lower()
    if app_mode == "api":
        print(f"\n Starting FastAPI backend at http://{API_HOST}:{API_PORT}/")
        subprocess.run(API_CMD)
    elif app_mode == "gradio":
        print("\n Starting Gradio UI...")
        subprocess.run([sys.executable, "run_gradio.py"])
    else:
        print(f" Unknown APP_MODE '{app_mode}'. Valid options: 'api', 'gradio'.")
        exit(1)


if __name__ == "__main__":
    main()
