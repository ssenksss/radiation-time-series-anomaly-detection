from typing import Optional

import pandas as pd

from db import fetch_one, fetch_all, execute_query, execute_many


def get_active_dataset_id() -> int:
    row = fetch_one(
        """
        SELECT value
        FROM app_settings
        WHERE key = 'active_dataset_id';
        """
    )

    if not row:
        raise RuntimeError("No active_dataset_id found in app_settings.")

    return int(row["value"])


def normalize_boolean(value) -> Optional[bool]:
    if value is None:
        return None

    text = str(value).strip().lower()

    if text in {"true", "1", "yes", "y"}:
        return True

    if text in {"false", "0", "no", "n"}:
        return False

    return None


def load_raw_measurements(dataset_id: int) -> pd.DataFrame:
    rows = fetch_all(
        """
        SELECT
            id,
            timestamp_raw,
            radiation_raw,
            sensor_id_raw,
            location_raw,
            temperature_raw,
            humidity_raw,
            is_anomaly_raw,
            anomaly_type_raw
        FROM raw_measurements
        WHERE dataset_id = %s
        ORDER BY id;
        """,
        (dataset_id,),
    )

    return pd.DataFrame(rows)


def clean_raw_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty:
        raise RuntimeError("No raw measurements found for the active dataset.")

    cleaned = dataframe.copy()

    cleaned["timestamp"] = pd.to_datetime(cleaned["timestamp_raw"], errors="coerce")
    cleaned["radiation_level"] = pd.to_numeric(cleaned["radiation_raw"], errors="coerce")
    cleaned["temperature"] = pd.to_numeric(cleaned["temperature_raw"], errors="coerce")
    cleaned["humidity"] = pd.to_numeric(cleaned["humidity_raw"], errors="coerce")
    cleaned["original_label"] = cleaned["is_anomaly_raw"].apply(normalize_boolean)

    cleaned["sensor_id"] = cleaned["sensor_id_raw"].astype(str)
    cleaned["location"] = cleaned["location_raw"].astype(str)
    cleaned["anomaly_type"] = cleaned["anomaly_type_raw"].astype(str)

    cleaned = cleaned.dropna(subset=["timestamp", "radiation_level"])
    cleaned = cleaned.sort_values("timestamp").reset_index(drop=True)

    cleaned["temperature"] = cleaned["temperature"].fillna(cleaned["temperature"].median())
    cleaned["humidity"] = cleaned["humidity"].fillna(cleaned["humidity"].median())

    return cleaned[
        [
            "timestamp",
            "radiation_level",
            "sensor_id",
            "location",
            "temperature",
            "humidity",
            "original_label",
            "anomaly_type",
        ]
    ]


def replace_clean_measurements(dataset_id: int, cleaned: pd.DataFrame) -> None:
    execute_query(
        """
        DELETE FROM clean_measurements
        WHERE dataset_id = %s;
        """,
        (dataset_id,),
    )

    rows = []

    for _, item in cleaned.iterrows():
        rows.append(
            (
                dataset_id,
                item["timestamp"].to_pydatetime(),
                float(item["radiation_level"]),
                item["sensor_id"],
                item["location"],
                float(item["temperature"]) if pd.notna(item["temperature"]) else None,
                float(item["humidity"]) if pd.notna(item["humidity"]) else None,
                item["original_label"],
                item["anomaly_type"],
            )
        )

    execute_many(
        """
        INSERT INTO clean_measurements (
            dataset_id,
            timestamp,
            radiation_level,
            sensor_id,
            location,
            temperature,
            humidity,
            original_label,
            anomaly_type
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """,
        rows,
    )


def preprocess_active_dataset() -> int:
    dataset_id = get_active_dataset_id()

    raw_dataframe = load_raw_measurements(dataset_id)
    cleaned_dataframe = clean_raw_dataframe(raw_dataframe)
    replace_clean_measurements(dataset_id, cleaned_dataframe)

    execute_query(
        """
        UPDATE datasets
        SET status = 'cleaned',
            row_count = %s
        WHERE id = %s;
        """,
        (len(cleaned_dataframe), dataset_id),
    )

    print("Data preprocessing completed successfully.")
    print(f"Dataset ID: {dataset_id}")
    print(f"Rows inserted into clean_measurements: {len(cleaned_dataframe)}")

    return dataset_id


def main():
    preprocess_active_dataset()


if __name__ == "__main__":
    main()
