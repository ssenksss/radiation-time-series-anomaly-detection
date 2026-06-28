import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

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


def load_labeled_feature_measurements(dataset_id: int) -> pd.DataFrame:
    rows = fetch_all(
        """
        SELECT
            fm.id,
            fm.timestamp,
            fm.radiation_level,
            fm.temperature,
            fm.humidity,
            fm.hour_of_day,
            fm.day_of_week,
            fm.rolling_mean,
            fm.rolling_std,
            fm.radiation_diff,
            cm.original_label
        FROM feature_measurements fm
        JOIN clean_measurements cm
            ON fm.clean_measurement_id = cm.id
        WHERE fm.dataset_id = %s
          AND cm.original_label IS NOT NULL
        ORDER BY fm.timestamp;
        """,
        (dataset_id,),
    )

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        raise RuntimeError("No labeled feature measurements found. This dataset does not contain is_anomaly.")

    dataframe["timestamp"] = pd.to_datetime(dataframe["timestamp"])

    for column in FEATURE_COLUMNS:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    medians = dataframe[FEATURE_COLUMNS].median(numeric_only=True)
    dataframe[FEATURE_COLUMNS] = dataframe[FEATURE_COLUMNS].fillna(medians).fillna(0)

    dataframe["original_label"] = dataframe["original_label"].astype(bool).astype(int)

    if len(np.unique(dataframe["original_label"])) < 2:
        raise RuntimeError("Decision Tree requires both normal and anomaly examples.")

    return dataframe


def build_status(radiation_level: float, predicted_anomaly: bool, threshold: float) -> str:
    if not predicted_anomaly:
        return "normal"

    if threshold > 0 and radiation_level >= threshold * 2:
        return "critical"

    return "high"


def train_decision_tree(dataframe: pd.DataFrame, threshold: float) -> pd.DataFrame:
    model_dataframe = dataframe.copy()

    labels = model_dataframe["original_label"].astype(int)

    model = DecisionTreeClassifier(
        max_depth=6,
        class_weight="balanced",
        random_state=42,
    )

    model.fit(model_dataframe[FEATURE_COLUMNS], labels)

    predictions = model.predict(model_dataframe[FEATURE_COLUMNS]).astype(bool)
    scores = model.predict_proba(model_dataframe[FEATURE_COLUMNS])[:, 1]

    model_dataframe["predicted_anomaly"] = predictions
    model_dataframe["anomaly_score"] = scores
    model_dataframe["status"] = model_dataframe.apply(
        lambda row: build_status(float(row["radiation_level"]), bool(row["predicted_anomaly"]), threshold),
        axis=1,
    )

    print("Decision Tree training completed.")
    print(f"Detected anomalies: {int(model_dataframe['predicted_anomaly'].sum())}")

    return model_dataframe


def replace_decision_tree_results(dataset_id: int, results: pd.DataFrame) -> None:
    execute_query(
        """
        DELETE FROM anomaly_results
        WHERE dataset_id = %s
          AND model_name = 'Decision Tree';
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
                "Decision Tree",
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


def train_decision_tree_for_active_dataset() -> int:
    dataset_id = get_active_dataset_id()
    threshold = get_threshold()

    dataframe = load_labeled_feature_measurements(dataset_id)
    results = train_decision_tree(dataframe, threshold)
    replace_decision_tree_results(dataset_id, results)

    print("Decision Tree results written to anomaly_results.")
    return dataset_id


def main():
    train_decision_tree_for_active_dataset()


if __name__ == "__main__":
    main()