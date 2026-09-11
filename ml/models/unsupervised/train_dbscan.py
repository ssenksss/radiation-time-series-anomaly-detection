"""
dbscan anomaly detection model

this model groups dense regions of records
records that remain outside dense regions are treated as possible anomalies
"""

from pathlib import Path
import sys
import time
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = PROJECT_ROOT / "ml" / "scripts"

for import_path in (PROJECT_ROOT, SCRIPTS_DIR):
    if str(import_path) not in sys.path:
        sys.path.append(str(import_path))

from ml.models.model_training_utils import (
    FEATURE_COLUMNS,
    add_result_columns,
    build_timing,
    chronological_train_test_split,
    convert_feature_columns_to_numeric,
    fill_missing_features_from_train,
    get_active_dataset_id,
    load_feature_measurements,
    mark_dataset_as_model_trained,
    print_training_summary,
    replace_anomaly_results,
)


MODEL_NAME = "DBSCAN"

MIN_SAMPLES = 16
IQR_MULTIPLIER = 1.5


def calculate_eps(
    train_features: np.ndarray,
) -> Tuple[float, float, float, float]:

    neighbors = NearestNeighbors(
        n_neighbors=MIN_SAMPLES,
    )

    neighbors.fit(
        train_features
    )

    distances, _ = neighbors.kneighbors(
        train_features
    )

    k_distances = np.sort(
        distances[:, -1]
    )

    q1 = float(
        np.quantile(
            k_distances,
            0.25,
        )
    )

    q3 = float(
        np.quantile(
            k_distances,
            0.75,
        )
    )

    iqr = q3 - q1

    eps = (
        q3
        + IQR_MULTIPLIER
        * iqr
    )

    return eps, q1, q3, iqr


def calculate_anomaly_scores(
    features: np.ndarray,
    core_samples: np.ndarray,
    eps: float,
) -> np.ndarray:

    if len(core_samples) == 0:
        return np.ones(
            len(features),
            dtype=float,
        )

    nearest_core = NearestNeighbors(
        n_neighbors=1,
    )

    nearest_core.fit(
        core_samples
    )

    distances, _ = nearest_core.kneighbors(
        features
    )

    return (
        distances[:, 0]
        / max(eps, 1e-12)
    )


def train_dbscan(
    dataframe: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[str, float]]:

    model_dataframe = convert_feature_columns_to_numeric(
        dataframe.copy()
    )

    train_dataframe, test_dataframe = chronological_train_test_split(
        model_dataframe
    )

    train_ids = set(
        train_dataframe["id"].tolist()
    )

    test_ids = set(
        test_dataframe["id"].tolist()
    )

    train_dataframe, test_dataframe = fill_missing_features_from_train(
        train_dataframe,
        test_dataframe,
    )

    train_medians = train_dataframe[
        FEATURE_COLUMNS
    ].median(numeric_only=True)

    model_dataframe[FEATURE_COLUMNS] = (
        model_dataframe[FEATURE_COLUMNS]
        .fillna(train_medians)
        .fillna(0)
    )

    training_started_at = time.time()

    scaler = StandardScaler()

    train_features = scaler.fit_transform(
        train_dataframe[FEATURE_COLUMNS]
    )

    eps, q1, q3, iqr = calculate_eps(
        train_features
    )

    model = DBSCAN(
        eps=eps,
        min_samples=MIN_SAMPLES,
    )

    train_labels = model.fit_predict(
        train_features
    )

    core_sample_indices = model.core_sample_indices_

    if len(core_sample_indices) > 0:
        core_samples = train_features[
            core_sample_indices
        ]
    else:
        core_samples = np.empty(
            (
                0,
                train_features.shape[1],
            )
        )

    training_time_seconds = (
        time.time() - training_started_at
    )

    # prediction timing is measured only on the test set
    test_features = scaler.transform(
        test_dataframe[FEATURE_COLUMNS]
    )

    prediction_started_at = time.time()

    calculate_anomaly_scores(
        test_features,
        core_samples,
        eps,
    )

    prediction_time_seconds = (
        time.time() - prediction_started_at
    )

    # full scores are stored for the application
    all_features = scaler.transform(
        model_dataframe[FEATURE_COLUMNS]
    )

    anomaly_scores = calculate_anomaly_scores(
        all_features,
        core_samples,
        eps,
    )

    predicted_anomaly = (
        anomaly_scores > 1.0
    )

    results = add_result_columns(
        dataframe=model_dataframe,
        predicted_anomaly=predicted_anomaly,
        anomaly_scores=anomaly_scores,
    )

    results["evaluation_split"] = "full"

    results.loc[
        results["id"].isin(train_ids),
        "evaluation_split",
    ] = "train"

    results.loc[
        results["id"].isin(test_ids),
        "evaluation_split",
    ] = "test"

    clusters_found = len(
        set(train_labels)
        - {-1}
    )

    native_noise_points = int(
        np.sum(
            train_labels == -1
        )
    )

    print(
        f"DBSCAN features: {len(FEATURE_COLUMNS)}"
    )

    print(
        f"DBSCAN min_samples: {MIN_SAMPLES}"
    )

    print(
        f"DBSCAN k-distance Q1: {q1}"
    )

    print(
        f"DBSCAN k-distance Q3: {q3}"
    )

    print(
        f"DBSCAN k-distance IQR: {iqr}"
    )

    print(
        f"DBSCAN eps: {eps}"
    )

    print(
        f"DBSCAN clusters found on train: {clusters_found}"
    )

    print(
        f"DBSCAN core samples: {len(core_samples)}"
    )

    print(
        f"DBSCAN native train noise points: {native_noise_points}"
    )

    print(
        f"Train rows: {len(train_dataframe)}"
    )

    print(
        f"Test rows: {len(test_dataframe)}"
    )

    return results, build_timing(
        training_time_seconds,
        prediction_time_seconds,
    )


def train_dbscan_for_active_dataset() -> Dict[str, float]:

    dataset_id = get_active_dataset_id()

    feature_dataframe = load_feature_measurements(
        dataset_id
    )

    result_dataframe, timing = train_dbscan(
        feature_dataframe,
    )

    replace_anomaly_results(
        dataset_id,
        MODEL_NAME,
        result_dataframe,
    )

    mark_dataset_as_model_trained(
        dataset_id
    )

    print_training_summary(
        MODEL_NAME,
        dataset_id,
        result_dataframe,
    )

    return timing


def main():
    train_dbscan_for_active_dataset()


if __name__ == "__main__":
    main()