from pathlib import Path
import argparse

import pandas as pd

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

    dataset_id = row["id"]

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


def ingest_csv(csv_path: Path) -> int:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    dataframe = pd.read_csv(csv_path)

    dataset_id = create_dataset_record(
        name=csv_path.stem,
        original_filename=csv_path.name,
        row_count=len(dataframe),
    )

    insert_raw_measurements(dataset_id, dataframe)

    print("CSV ingest completed successfully.")
    print(f"Dataset ID: {dataset_id}")
    print(f"Rows inserted into raw_measurements: {len(dataframe)}")

    return dataset_id


def main():
    parser = argparse.ArgumentParser(description="Ingest radiation CSV into PostgreSQL raw table.")
    parser.add_argument(
        "--file",
        type=str,
        default=str(DEFAULT_CSV_PATH),
        help="Path to the CSV file that should be ingested.",
    )

    args = parser.parse_args()
    ingest_csv(Path(args.file))


if __name__ == "__main__":
    main()
