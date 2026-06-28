import numpy as np
import pandas as pd
from pyod.models.ecod import ECOD
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

MAX_CONTAMINATION = 0.20
FALLBACK_CONTAMINATION = 0.03


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
    filled[FEATURE_COLUMNS] = filled[FEATURE_COLUMNS].fillna(medians)
    filled[FEATURE_COLUMNS] = filled[FEATURE_COLUMNS].fillna(0)

    return filled


def calculate_contamination_from_threshold(dataframe: pd.DataFrame, threshold: float) -> float:
    if dataframe.empty:
        return FALLBACK_CONTAMINATION

    ratio_above_threshold = float((dataframe["radiation_level"] > threshold).mean())

    if ratio_above_threshold <= 0:
        return FALLBACK_CONTAMINATION

    return min(MAX_CONTAMINATION, ratio_above_threshold)


def load_feature_measurements(dataset_id: int) -> pd.DataFrame:
    rows = fetch_all(
        """
        SELECT
            id,
            timestamp,
            radiation_level,
            temperature,
            humidity,
            hour_of_day,
            day_of_week,
            rolling_mean,
            rolling_std,
            radiation_diff
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


def normalize_scores(scores: np.ndarray) -> np.ndarray:
    scores = np.asarray(scores, dtype=float)
    min_score = float(scores.min())
    max_score = float(scores.max())

    if max_score == min_score:
        return np.zeros_like(scores)

    return (scores - min_score) / (max_score - min_score)


def train_ecod(dataframe: pd.DataFrame, threshold: float) -> pd.DataFrame:
    model_dataframe = safe_fill_feature_columns(dataframe)
    contamination = calculate_contamination_from_threshold(model_dataframe, threshold)

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(model_dataframe[FEATURE_COLUMNS])

    model = ECOD(
        contamination=contamination,
    )

    model.fit(scaled_features)

    predicted_anomaly = model.labels_.astype(bool)
    anomaly_scores = normalize_scores(model.decision_scores_)

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

    print(f"Threshold used for ECOD severity: {threshold}")
    print(f"Calculated contamination: {contamination}")

    return model_dataframe


def replace_ecod_results(dataset_id: int, results: pd.DataFrame) -> None:
    execute_query(
        """
        DELETE FROM anomaly_results
        WHERE dataset_id = %s
          AND model_name = 'ECOD';
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
                "ECOD",
            )
        )

    execute_many(
        """
        INSERT INTO anomaly_results (
            dataset_id,
            feature_measurement_id,
            timestamp,
            radiation_level,
            predicted_anomaly,
            anomaly_score,
            status,
            model_name
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """,
        rows,
    )


def train_ecod_for_active_dataset() -> int:
    dataset_id = get_active_dataset_id()
    threshold = get_threshold()

    feature_dataframe = load_feature_measurements(dataset_id)
    result_dataframe = train_ecod(feature_dataframe, threshold)
    replace_ecod_results(dataset_id, result_dataframe)

    total_anomalies = int(result_dataframe["predicted_anomaly"].sum())

    execute_query(
        """
        UPDATE datasets
        SET status = 'model_trained'
        WHERE id = %s;
        """,
        (dataset_id,),
    )

    print("ECOD training completed successfully.")
    print(f"Dataset ID: {dataset_id}")
    print(f"Rows inserted into anomaly_results: {len(result_dataframe)}")
    print(f"Detected anomalies: {total_anomalies}")

    return dataset_id


def main():
    train_ecod_for_active_dataset()


if __name__ == "__main__":
    main()