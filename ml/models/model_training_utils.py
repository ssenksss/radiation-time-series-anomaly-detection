from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Tuple

import numpy as np
import pandas as pd

from db import fetch_one, fetch_all, execute_query, execute_many


# features that go into the models
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
RANDOM_STATE = 42
TRAIN_RATIO = 0.70


def get_active_dataset_id() -> int:
    # get dataset selected in the app
    row = fetch_one("SELECT value FROM app_settings WHERE key = 'active_dataset_id';")

    if not row:
        raise RuntimeError("No active_dataset_id found in app_settings.")

    return int(row["value"])


def get_threshold() -> float:
    # use default threshold if there is no saved value
    row = fetch_one("SELECT value FROM app_settings WHERE key = 'threshold';")
    return float(row["value"]) if row else 0.18


def load_feature_measurements(dataset_id: int) -> pd.DataFrame:
    # read prepared feature data from database
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


def chronological_train_test_split(
        dataframe: pd.DataFrame,
        train_ratio: float = TRAIN_RATIO,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    split data in time order

    first rows are used for training and later rows are used for testing
    """
    ordered_dataframe = dataframe.sort_values("timestamp").reset_index(drop=True)

    split_index = int(len(ordered_dataframe) * train_ratio)

    if split_index <= 0 or split_index >= len(ordered_dataframe):
        raise RuntimeError("Not enough records for chronological train/test split.")

    train_dataframe = ordered_dataframe.iloc[:split_index].copy()
    test_dataframe = ordered_dataframe.iloc[split_index:].copy()

    return train_dataframe, test_dataframe


def safe_fill_feature_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    # models need numeric values without missing data
    filled = dataframe.copy()

    for column in FEATURE_COLUMNS:
        filled[column] = pd.to_numeric(filled[column], errors="coerce")

    medians = filled[FEATURE_COLUMNS].median(numeric_only=True)
    filled[FEATURE_COLUMNS] = filled[FEATURE_COLUMNS].fillna(medians).fillna(0)

    return filled


def calculate_contamination_from_threshold(dataframe: pd.DataFrame, threshold: float) -> float:
    """
    estimate expected anomaly ratio from the selected threshold

    some unsupervised models use this value as contamination
    """
    if dataframe.empty or "radiation_level" not in dataframe.columns:
        return FALLBACK_CONTAMINATION

    ratio_above_threshold = float((dataframe["radiation_level"] > threshold).mean())

    if ratio_above_threshold <= 0:
        return FALLBACK_CONTAMINATION

    return min(MAX_CONTAMINATION, ratio_above_threshold)


def normalize_scores(scores: Iterable[float]) -> np.ndarray:
    # scale scores to 0-1 when needed
    values = np.asarray(scores, dtype=float)

    if len(values) == 0:
        return values

    min_value = float(values.min())
    max_value = float(values.max())

    if max_value == min_value:
        return np.zeros_like(values)

    return (values - min_value) / (max_value - min_value)


def build_top_score_predictions(scores: Iterable[float], contamination: float) -> np.ndarray:
    """
    mark records with the highest scores as anomalies

    used for models that return scores instead of direct labels
    """
    values = np.asarray(scores, dtype=float)

    if len(values) == 0:
        return np.array([], dtype=bool)

    anomaly_count = max(1, int(round(len(values) * contamination)))
    anomaly_count = min(len(values), anomaly_count)

    threshold_index = len(values) - anomaly_count
    score_threshold = np.partition(values, threshold_index)[threshold_index]

    return values >= score_threshold


def build_status(radiation_level: float, predicted_anomaly: bool, threshold: float) -> str:
    # status is used later in the dashboard
    if not predicted_anomaly:
        return "normal"

    if threshold > 0 and radiation_level >= threshold * 2:
        return "critical"

    return "high"


def add_result_columns(
        dataframe: pd.DataFrame,
        predicted_anomaly: Iterable[bool],
        anomaly_scores: Iterable[float],
        threshold: float,
) -> pd.DataFrame:
    # prepare columns for anomaly_results table
    results = dataframe.copy()
    results["predicted_anomaly"] = np.asarray(predicted_anomaly).astype(bool)
    results["anomaly_score"] = np.asarray(anomaly_scores, dtype=float)

    results["status"] = results.apply(
        lambda row: build_status(
            float(row["radiation_level"]),
            bool(row["predicted_anomaly"]),
            threshold,
        ),
        axis=1,
    )

    return results


def replace_anomaly_results(dataset_id: int, model_name: str, results: pd.DataFrame) -> None:
    # remove old rows before saving new model results
    execute_query(
        """
        DELETE FROM anomaly_results
        WHERE dataset_id = %s
          AND model_name = %s;
        """,
        (dataset_id, model_name),
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
                model_name,
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


def mark_dataset_as_model_trained(dataset_id: int) -> None:
    # update dataset status after model training
    execute_query(
        """
        UPDATE datasets
        SET status = 'model_trained'
        WHERE id = %s;
        """,
        (dataset_id,),
    )


def build_timing(
        training_time_seconds: Optional[float],
        prediction_time_seconds: Optional[float],
) -> Dict[str, Any]:
    # save training and prediction duration
    return {
        "training_time_seconds": round(float(training_time_seconds), 6)
        if training_time_seconds is not None
        else None,
        "prediction_time_seconds": round(float(prediction_time_seconds), 6)
        if prediction_time_seconds is not None
        else None,
    }


def print_training_summary(model_name: str, dataset_id: int, results: pd.DataFrame) -> None:
    total_anomalies = int(results["predicted_anomaly"].sum())

    print(f"{model_name} training completed successfully.")
    print(f"Dataset ID: {dataset_id}")
    print(f"Rows inserted into anomaly_results: {len(results)}")
    print(f"Detected anomalies: {total_anomalies}")