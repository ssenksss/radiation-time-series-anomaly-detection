"""
local outlier factor anomaly detection model

this model compares the local density of each record with the density of its neighbors
records in much sparser areas are treated as possible anomalies
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

import pandas as pd
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

from ml.models.model_training_utils import (
    FEATURE_COLUMNS,
    add_result_columns,
    build_timing,
    calculate_contamination_from_threshold,
    chronological_train_test_split,
    get_active_dataset_id,
    get_threshold,
    load_feature_measurements,
    mark_dataset_as_model_trained,
    print_training_summary,
    replace_anomaly_results,
    safe_fill_feature_columns,
)


MODEL_NAME = "Local Outlier Factor"


def train_lof(dataframe: pd.DataFrame, threshold: float) -> Tuple[pd.DataFrame, Dict[str, float]]:
    model_dataframe = safe_fill_feature_columns(dataframe)
    train_dataframe, test_dataframe = chronological_train_test_split(model_dataframe)

    contamination = calculate_contamination_from_threshold(train_dataframe, threshold)

    # number of neighbors is adjusted to dataset size
    n_neighbors = min(35, max(5, len(train_dataframe) // 50))
    n_neighbors = min(n_neighbors, max(2, len(train_dataframe) - 1))

    training_started_at = time.time()

    # novelty mode allows lof to score rows after fitting
    scaler = StandardScaler()
    train_features = scaler.fit_transform(train_dataframe[FEATURE_COLUMNS])
    all_features = scaler.transform(model_dataframe[FEATURE_COLUMNS])

    # lof compares local density with neighboring records
    model = LocalOutlierFactor(
        n_neighbors=n_neighbors,
        contamination=contamination,
        novelty=True,
    )
    model.fit(train_features)

    training_time_seconds = time.time() - training_started_at

    prediction_started_at = time.time()
    predictions = model.predict(all_features)

    # negative decision score is used so larger score means more anomalous
    anomaly_scores = -model.decision_function(all_features)
    prediction_time_seconds = time.time() - prediction_started_at

    results = add_result_columns(
        dataframe=model_dataframe,
        predicted_anomaly=predictions == -1,
        anomaly_scores=anomaly_scores,
        threshold=threshold,
    )

    print(f"Threshold used for LOF sensitivity: {threshold}")
    print(f"Calculated contamination: {contamination}")
    print(f"LOF n_neighbors: {n_neighbors}")
    print(f"Train rows: {len(train_dataframe)}")
    print(f"Test rows: {len(test_dataframe)}")

    return results, build_timing(training_time_seconds, prediction_time_seconds)


def train_lof_for_active_dataset() -> Dict[str, float]:
    dataset_id = get_active_dataset_id()
    threshold = get_threshold()

    feature_dataframe = load_feature_measurements(dataset_id)
    result_dataframe, timing = train_lof(feature_dataframe, threshold)
    replace_anomaly_results(dataset_id, MODEL_NAME, result_dataframe)
    mark_dataset_as_model_trained(dataset_id)

    print_training_summary(MODEL_NAME, dataset_id, result_dataframe)

    return timing


def main():
    train_lof_for_active_dataset()


if __name__ == "__main__":
    main()
