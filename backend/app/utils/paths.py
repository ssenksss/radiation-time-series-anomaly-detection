from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = APP_DIR.parent
DATA_DIR = APP_DIR / "data"

DEFAULT_DATASET_PATH = DATA_DIR / "mock_radiation_measurements.csv"