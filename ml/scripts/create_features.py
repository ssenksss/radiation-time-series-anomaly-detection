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


def fill_numeric_with_safe_median(series: pd.Series, default_value: float = 0.0) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    median = numeric.median()

    if pd.isna(median):
        median = default_value

    return numeric.fillna(median)


def load_clean_measurements(dataset_id: int) -> pd.DataFrame:
    rows = fetch_all(
        """
        SELECT
            id,
            timestamp,
            radiation_level,
            sensor_id,
            location,
            temperature,
            humidity,
            original_label,
            anomaly_type
        FROM clean_measurements
        WHERE dataset_id = %s
        ORDER BY timestamp;
        """,
        (dataset_id,),
    )

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        raise RuntimeError("No clean measurements found. Run data_preprocessing.py first.")

    dataframe["timestamp"] = pd.to_datetime(dataframe["timestamp"])

    return dataframe


def build_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    features = dataframe.copy()

    features = features.sort_values(["sensor_id", "timestamp"]).reset_index(drop=True)

    features["radiation_level"] = pd.to_numeric(features["radiation_level"], errors="coerce")
    features["temperature"] = fill_numeric_with_safe_median(features["temperature"], default_value=0.0)
    features["humidity"] = fill_numeric_with_safe_median(features["humidity"], default_value=0.0)

    features = features.dropna(subset=["radiation_level"])
    features = features.reset_index(drop=True)

    features["hour_of_day"] = features["timestamp"].dt.hour
    features["day_of_week"] = features["timestamp"].dt.dayofweek

    features["rolling_mean"] = (
        features.groupby("sensor_id")["radiation_level"]
        .transform(lambda series: series.rolling(window=12, min_periods=1).mean())
    )

    features["rolling_std"] = (
        features.groupby("sensor_id")["radiation_level"]
        .transform(lambda series: series.rolling(window=12, min_periods=1).std())
    )

    features["radiation_diff"] = (
        features.groupby("sensor_id")["radiation_level"]
        .diff()
    )

    features["rolling_std"] = features["rolling_std"].fillna(0)
    features["radiation_diff"] = features["radiation_diff"].fillna(0)

    features["rolling_mean"] = fill_numeric_with_safe_median(
        features["rolling_mean"],
        default_value=float(features["radiation_level"].mean()),
    )

    return features


def replace_feature_measurements(dataset_id: int, features: pd.DataFrame) -> None:
    execute_query(
        """
        DELETE FROM feature_measurements
        WHERE dataset_id = %s;
        """,
        (dataset_id,),
    )

    rows = []

    for _, item in features.iterrows():
        rows.append(
            (
                dataset_id,
                int(item["id"]),
                item["timestamp"].to_pydatetime(),
                float(item["radiation_level"]),
                float(item["temperature"]) if pd.notna(item["temperature"]) else None,
                float(item["humidity"]) if pd.notna(item["humidity"]) else None,
                int(item["hour_of_day"]),
                int(item["day_of_week"]),
                float(item["rolling_mean"]),
                float(item["rolling_std"]),
                float(item["radiation_diff"]),
            )
        )

    execute_many(
        """
        INSERT INTO feature_measurements (
            dataset_id,
            clean_measurement_id,
            timestamp,
            radiation_level,
            temperature,
            humidity,
            hour_of_day,
            day_of_week,
            rolling_mean,
            rolling_std,
            radiation_diff
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """,
        rows,
    )


def create_features_for_active_dataset() -> int:
    dataset_id = get_active_dataset_id()

    clean_dataframe = load_clean_measurements(dataset_id)
    feature_dataframe = build_features(clean_dataframe)
    replace_feature_measurements(dataset_id, feature_dataframe)

    execute_query(
        """
        UPDATE datasets
        SET status = 'features_created'
        WHERE id = %s;
        """,
        (dataset_id,),
    )

    print("Feature engineering completed successfully.")
    print(f"Dataset ID: {dataset_id}")
    print(f"Rows inserted into feature_measurements: {len(feature_dataframe)}")

    return dataset_id


def main():
    create_features_for_active_dataset()


if __name__ == "__main__":
    main()