"""
pca reconstruction anomaly detection model

this model learns a compressed representation of normal measurements
records with larger reconstruction error are treated as possible anomalies
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
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from ml.models.model_training_utils import (
    FEATURE_COLUMNS,
    RANDOM_STATE,
    add_result_columns,
    build_timing,
    build_top_score_predictions,
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


MODEL_NAME = "PCA Reconstruction Error"


def train_pca_reconstruction(dataframe: pd.DataFrame, threshold: float) -> Tuple[pd.DataFrame, Dict[str, float]]:
    model_dataframe = safe_fill_feature_columns(dataframe)
    train_dataframe, test_dataframe = chronological_train_test_split(model_dataframe)

    contamination = calculate_contamination_from_threshold(train_dataframe, threshold)

    # contamination decides how many largest reconstruction errors are marked
    training_started_at = time.time()

    scaler = StandardScaler()
    train_features = scaler.fit_transform(train_dataframe[FEATURE_COLUMNS])
    all_features = scaler.transform(model_dataframe[FEATURE_COLUMNS])
    # use a small number of components to keep only the main pattern
    n_components = min(3, train_features.shape[1] - 1)

    model = PCA(
        n_components=n_components,
        random_state=RANDOM_STATE,
    )
    model.fit(train_features)

    training_time_seconds = time.time() - training_started_at

    prediction_started_at = time.time()
    transformed = model.transform(all_features)
    reconstructed = model.inverse_transform(transformed)
    # reconstruction error is used as anomaly score
    anomaly_scores = np.mean((all_features - reconstructed) ** 2, axis=1)
    predicted_anomaly = build_top_score_predictions(anomaly_scores, contamination)
    prediction_time_seconds = time.time() - prediction_started_at

    results = add_result_columns(
        dataframe=model_dataframe,
        predicted_anomaly=predicted_anomaly,
        anomaly_scores=anomaly_scores,
        threshold=threshold,
    )

    print(f"Threshold used for PCA Reconstruction severity: {threshold}")
    print(f"PCA components: {n_components}")
    print(f"Calculated contamination: {contamination}")
    print(f"Train rows: {len(train_dataframe)}")
    print(f"Test rows: {len(test_dataframe)}")

    return results, build_timing(training_time_seconds, prediction_time_seconds)


def train_pca_reconstruction_for_active_dataset() -> Dict[str, float]:
    dataset_id = get_active_dataset_id()
    threshold = get_threshold()

    feature_dataframe = load_feature_measurements(dataset_id)
    result_dataframe, timing = train_pca_reconstruction(feature_dataframe, threshold)
    replace_anomaly_results(dataset_id, MODEL_NAME, result_dataframe)
    mark_dataset_as_model_trained(dataset_id)

    print_training_summary(MODEL_NAME, dataset_id, result_dataframe)

    return timing


def main():
    train_pca_reconstruction_for_active_dataset()


if __name__ == "__main__":
    main()
