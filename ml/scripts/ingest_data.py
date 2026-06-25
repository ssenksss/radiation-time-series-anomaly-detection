from pathlib import Path
import argparse
import tempfile
import zipfile

import pandas as pd

from csv_column_mapper import standardize_radiation_csv
from db import fetch_one, execute_query, execute_many


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CSV_PATH = ROOT_DIR / "backend" / "app" / "data" / "mock_radiation_measurements.csv"


def create_dataset_record(name: str, original_filename: str, row_count: int) -> int:
    row = fetch_one(
        """
        INSERT INTO datasets (name, original_filename, source_type, row_count, status, is_active)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (name, original_filename, "csv", row_count, "raw_loaded", True),
    )

    dataset_id = int(row["id"])

    execute_query(
        """
        UPDATE datasets
        SET is_active = FALSE
        WHERE id <> %s;
        """,
        (dataset_id,),
    )

    execute_query(
        """
        INSERT INTO app_settings (key, value)
        VALUES ('active_dataset_id', %s)
        ON CONFLICT (key) DO UPDATE
        SET value = EXCLUDED.value,
            updated_at = CURRENT_TIMESTAMP;
        """,
        (str(dataset_id),),
    )

    return dataset_id


def insert_raw_measurements(dataset_id: int, dataframe: pd.DataFrame) -> None:
    rows = []

    for _, item in dataframe.iterrows():
        rows.append(
            (
                dataset_id,
                str(item.get("timestamp", "")),
                str(item.get("radiation_uSv_h", "")),
                str(item.get("sensor_id", "")),
                str(item.get("location", "")),
                str(item.get("temperature_c", "")),
                str(item.get("humidity_percent", "")),
                str(item.get("is_anomaly", "")),
                str(item.get("anomaly_type", "")),
            )
        )

    if not rows:
        raise RuntimeError("No rows available for raw_measurements insert.")

    execute_many(
        """
        INSERT INTO raw_measurements (
            dataset_id,
            timestamp_raw,
            radiation_raw,
            sensor_id_raw,
            location_raw,
            temperature_raw,
            humidity_raw,
            is_anomaly_raw,
            anomaly_type_raw
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """,
        rows,
    )


def is_supported_csv_member(member_name: str) -> bool:
    normalized = member_name.replace("\\", "/")
    parts = normalized.split("/")
    filename = parts[-1]

    if not filename:
        return False

    if "__MACOSX" in parts:
        return False

    if filename.startswith("._"):
        return False

    return filename.lower().endswith(".csv")


def load_standardized_csv_from_zip(zip_path: Path) -> pd.DataFrame:
    frames = []

    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)

        with zipfile.ZipFile(zip_path) as archive:
            csv_members = [
                member
                for member in archive.namelist()
                if is_supported_csv_member(member)
            ]

            if not csv_members:
                raise RuntimeError("ZIP file does not contain any supported CSV files.")

            for index, member in enumerate(csv_members, start=1):
                original_name = Path(member).name
                safe_name = f"{index:03d}_{original_name}"
                extracted_path = temporary_root / safe_name
                extracted_path.write_bytes(archive.read(member))

                standardized = standardize_radiation_csv(extracted_path)

                if "location" in standardized.columns:
                    extracted_stem = Path(original_name).stem.replace("_", " ").replace("-", " ").strip()
                    generated_location = extracted_path.stem.replace("_", " ").replace("-", " ").strip()

                    standardized.loc[
                        standardized["location"].astype(str).str.strip().eq(generated_location),
                        "location",
                    ] = extracted_stem

                if "sensor_id" in standardized.columns:
                    original_sensor = Path(original_name).stem.upper().replace(" ", "_").replace("-", "_")
                    generated_sensor = extracted_path.stem.upper().replace(" ", "_").replace("-", "_")

                    standardized.loc[
                        standardized["sensor_id"].astype(str).str.strip().eq(generated_sensor),
                        "sensor_id",
                    ] = original_sensor

                frames.append(standardized)

    if not frames:
        raise RuntimeError("No valid CSV rows were found inside the ZIP file.")

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values(["location", "timestamp"]).reset_index(drop=True)

    if combined.empty:
        raise RuntimeError("ZIP was read, but no valid rows remained after cleaning.")

    return combined


def standardize_dataset_file(dataset_path: Path) -> pd.DataFrame:
    suffix = dataset_path.suffix.lower()

    if suffix == ".csv":
        return standardize_radiation_csv(dataset_path)

    if suffix == ".zip":
        return load_standardized_csv_from_zip(dataset_path)

    raise RuntimeError("Only CSV and ZIP files containing CSV files are supported.")


def ingest_csv(csv_path: Path) -> int:
    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {csv_path}")

    standardized_dataframe = standardize_dataset_file(csv_path)

    dataset_id = create_dataset_record(
        name=csv_path.stem,
        original_filename=csv_path.name,
        row_count=len(standardized_dataframe),
    )

    insert_raw_measurements(dataset_id, standardized_dataframe)

    print("Dataset ingest completed successfully.")
    print(f"Dataset file: {csv_path}")
    print(f"Dataset ID: {dataset_id}")
    print(f"Rows inserted into raw_measurements: {len(standardized_dataframe)}")
    print("Columns were mapped to the standard internal radiation format.")

    return dataset_id


def main():
    parser = argparse.ArgumentParser(description="Ingest radiation CSV or ZIP into PostgreSQL raw table.")

    parser.add_argument(
        "--file",
        type=str,
        default=str(DEFAULT_CSV_PATH),
        help="Path to the CSV file or ZIP file that should be ingested.",
    )

    args = parser.parse_args()
    ingest_csv(Path(args.file))


if __name__ == "__main__":
    main()