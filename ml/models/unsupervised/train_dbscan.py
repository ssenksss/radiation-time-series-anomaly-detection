"""
dbscan clustering anomaly detection model

dbscan groups dense regions of measurements
records marked as noise are treated as possible anomalies
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = PROJECT_ROOT / "ml" / "scripts"

for import_path in (PROJECT_ROOT, SCRIPTS_DIR):
    if str(import_path) not in sys.path:
        sys.path.append(str(import_path))

import time
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

from ml.models.model_training_utils import (
    FEATURE_COLUMNS,
    add_result_columns,
    build_timing,
    chronological_train_test_split,
    get_active_dataset_id,
    get_threshold,
    load_feature_measurements,
    mark_dataset_as_model_trained,
    print_training_summary,
    replace_anomaly_results,
    safe_fill_feature_columns,
)


MODEL_NAME = "DBSCAN"


def train_dbscan(dataframe: pd.DataFrame, threshold: float) -> Tuple[pd.DataFrame, Dict[str, float]]:
    model_dataframe = safe_fill_feature_columns(dataframe)
    train_dataframe, test_dataframe = chronological_train_test_split(model_dataframe)

    training_started_at = time.time()

    # scaler is fitted on train data, but dbscan itself is used as a clustering baseline
    scaler = StandardScaler()
    scaler.fit(train_dataframe[FEATURE_COLUMNS])
    all_features = scaler.transform(model_dataframe[FEATURE_COLUMNS])

    model = DBSCAN(
        eps=1.8,
        min_samples=10,
        n_jobs=-1,
    )
    labels = model.fit_predict(all_features)

    training_time_seconds = time.time() - training_started_at

    prediction_started_at = time.time()
    predicted_anomaly = labels == -1

    center = np.mean(all_features, axis=0)
    anomaly_scores = np.linalg.norm(all_features - center, axis=1)

    if not predicted_anomaly.any():
        anomaly_count = max(1, int(len(model_dataframe) * 0.03))
        score_threshold = np.partition(anomaly_scores, -anomaly_count)[-anomaly_count]
        predicted_anomaly = anomaly_scores >= score_threshold

    prediction_time_seconds = time.time() - prediction_started_at

    results = add_result_columns(
        dataframe=model_dataframe,
        predicted_anomaly=predicted_anomaly,
        anomaly_scores=anomaly_scores,
        threshold=threshold,
    )

    print(f"Threshold used for DBSCAN severity: {threshold}")
    print("DBSCAN uses fit_predict because it is a clustering baseline without a native predict method.")
    print(f"DBSCAN detected anomalies: {int(results['predicted_anomaly'].sum())}")
    print(f"Train rows: {len(train_dataframe)}")
    print(f"Test rows: {len(test_dataframe)}")

    return results, build_timing(training_time_seconds, prediction_time_seconds)


def train_dbscan_for_active_dataset() -> Dict[str, float]:
    dataset_id = get_active_dataset_id()
    threshold = get_threshold()

    feature_dataframe = load_feature_measurements(dataset_id)
    result_dataframe, timing = train_dbscan(feature_dataframe, threshold)
    replace_anomaly_results(dataset_id, MODEL_NAME, result_dataframe)
    mark_dataset_as_model_trained(dataset_id)

    print_training_summary(MODEL_NAME, dataset_id, result_dataframe)

    return timing


def main():
    train_dbscan_for_active_dataset()


if __name__ == "__main__":
    main()
