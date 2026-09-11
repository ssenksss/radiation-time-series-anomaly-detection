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

RANDOM_STATE = 42
TRAIN_RATIO = 0.70


def get_active_dataset_id() -> int:
    # get dataset selected in the app
    row = fetch_one("SELECT value FROM app_settings WHERE key = 'active_dataset_id';")

    if not row:
        raise RuntimeError("No active_dataset_id found in app_settings.")

    return int(row["value"])





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


def convert_feature_columns_to_numeric(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    # convert model features to numeric values
    converted = dataframe.copy()

    for column in FEATURE_COLUMNS:
        converted[column] = pd.to_numeric(
            converted[column],
            errors="coerce",
        )

    return converted


def fill_missing_features_from_train(
    train_dataframe: pd.DataFrame,
    other_dataframe: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    # calculate replacement values only from training data
    train_filled = train_dataframe.copy()
    other_filled = other_dataframe.copy()

    train_medians = train_filled[FEATURE_COLUMNS].median(
        numeric_only=True
    )

    train_filled[FEATURE_COLUMNS] = (
        train_filled[FEATURE_COLUMNS]
        .fillna(train_medians)
        .fillna(0)
    )

    other_filled[FEATURE_COLUMNS] = (
        other_filled[FEATURE_COLUMNS]
        .fillna(train_medians)
        .fillna(0)
    )

    return train_filled, other_filled



def add_result_columns(
        dataframe: pd.DataFrame,
        predicted_anomaly: Iterable[bool],
        anomaly_scores: Iterable[float],
        ) -> pd.DataFrame:
    # prepare columns for anomaly_results table
    results = dataframe.copy()

    results["predicted_anomaly"] = np.asarray(
        predicted_anomaly
    ).astype(bool)

    results["anomaly_score"] = np.asarray(
        anomaly_scores,
        dtype=float,
    )

    return results

def replace_anomaly_results(
    dataset_id: int,
    model_name: str,
    results: pd.DataFrame,
) -> None:
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
        model_name,
        str(item.get("evaluation_split", "full")),
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
            model_name,
            evaluation_split
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