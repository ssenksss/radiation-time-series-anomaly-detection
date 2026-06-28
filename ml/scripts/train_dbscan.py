import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

from db import fetch_one, fetch_all, execute_query, execute_many


FEATURE_COLUMNS = [
    "radiation_level",
    "temperature",
    "humidity",
    "hour_of_day",
    "day_of_week",
    "rolling_mean",
    "rolling_std",
    "radiation_diff",
]


def get_active_dataset_id() -> int:
    row = fetch_one("SELECT value FROM app_settings WHERE key = 'active_dataset_id';")
    if not row:
        raise RuntimeError("No active_dataset_id found in app_settings.")
    return int(row["value"])


def get_threshold() -> float:
    row = fetch_one("SELECT value FROM app_settings WHERE key = 'threshold';")
    return float(row["value"]) if row else 0.18


def safe_fill_feature_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    filled = dataframe.copy()
    for column in FEATURE_COLUMNS:
        filled[column] = pd.to_numeric(filled[column], errors="coerce")
    medians = filled[FEATURE_COLUMNS].median(numeric_only=True)
    filled[FEATURE_COLUMNS] = filled[FEATURE_COLUMNS].fillna(medians).fillna(0)
    return filled


def load_feature_measurements(dataset_id: int) -> pd.DataFrame:
    rows = fetch_all(
        """
        SELECT id, timestamp, radiation_level, temperature, humidity,
               hour_of_day, day_of_week, rolling_mean, rolling_std, radiation_diff
        FROM feature_measurements
        WHERE dataset_id = %s
        ORDER BY timestamp;
        """,
        (dataset_id,),
    )

    dataframe = pd.DataFrame(rows)
    if dataframe.empty:
        raise RuntimeError("No feature measurements found. Run create_features.py first.")

    dataframe["timestamp"] = pd.to_datetime(dataframe["timestamp"])
    return dataframe


def train_dbscan(dataframe: pd.DataFrame, threshold: float) -> pd.DataFrame:
    model_dataframe = safe_fill_feature_columns(dataframe)

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(model_dataframe[FEATURE_COLUMNS])

    model = DBSCAN(
        eps=1.8,
        min_samples=10,
        n_jobs=-1,
    )

    labels = model.fit_predict(scaled_features)
    predicted_anomaly = labels == -1

    center = np.mean(scaled_features, axis=0)
    anomaly_scores = np.linalg.norm(scaled_features - center, axis=1)

    if not predicted_anomaly.any():
        anomaly_count = max(1, int(len(model_dataframe) * 0.03))
        score_threshold = np.partition(anomaly_scores, -anomaly_count)[-anomaly_count]
        predicted_anomaly = anomaly_scores >= score_threshold

    model_dataframe["predicted_anomaly"] = predicted_anomaly
    model_dataframe["anomaly_score"] = anomaly_scores

    def build_status(row) -> str:
        if not bool(row["predicted_anomaly"]):
            return "normal"

        radiation_level = float(row["radiation_level"])

        if threshold > 0 and radiation_level >= threshold * 2:
            return "critical"

        return "high"

    model_dataframe["status"] = model_dataframe.apply(build_status, axis=1)

    print(f"Threshold used for DBSCAN severity: {threshold}")
    print(f"DBSCAN detected anomalies: {int(model_dataframe['predicted_anomaly'].sum())}")

    return model_dataframe


def replace_dbscan_results(dataset_id: int, results: pd.DataFrame) -> None:
    execute_query(
        """
        DELETE FROM anomaly_results
        WHERE dataset_id = %s
          AND model_name = 'DBSCAN';
        """,
        (dataset_id,),
    )

    rows = []

    for _, item in results.iterrows():
        rows.append(
            (
                dataset_id,
                int(item["id"]),
                item["timestamp"].to_pydatetime(),
                float(item["radiation_level"]),
                bool(item["predicted_anomaly"]),
                float(item["anomaly_score"]),
                str(item["status"]),
                "DBSCAN",
            )
        )

    execute_many(
        """
        INSERT INTO anomaly_results (
            dataset_id, feature_measurement_id, timestamp, radiation_level,
            predicted_anomaly, anomaly_score, status, model_name
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """,
        rows,
    )


def train_dbscan_for_active_dataset() -> int:
    dataset_id = get_active_dataset_id()
    threshold = get_threshold()

    feature_dataframe = load_feature_measurements(dataset_id)
    result_dataframe = train_dbscan(feature_dataframe, threshold)
    replace_dbscan_results(dataset_id, result_dataframe)

    total_anomalies = int(result_dataframe["predicted_anomaly"].sum())

    execute_query("UPDATE datasets SET status = 'model_trained' WHERE id = %s;", (dataset_id,))

    print("DBSCAN training completed successfully.")
    print(f"Dataset ID: {dataset_id}")
    print(f"Rows inserted into anomaly_results: {len(result_dataframe)}")
    print(f"Detected anomalies: {total_anomalies}")

    return dataset_id


def main():
    train_dbscan_for_active_dataset()


if __name__ == "__main__":
    main()