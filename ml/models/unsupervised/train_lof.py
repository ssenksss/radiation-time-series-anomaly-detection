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
    chronological_train_test_split,
    convert_feature_columns_to_numeric,
    fill_missing_features_from_train,
    get_active_dataset_id,
    load_feature_measurements,
    mark_dataset_as_model_trained,
    print_training_summary,
    replace_anomaly_results,
)


MODEL_NAME = "Local Outlier Factor"

N_NEIGHBORS = 20


def train_lof(
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

    model = LocalOutlierFactor(
        n_neighbors=N_NEIGHBORS,
        novelty=True,
        contamination="auto",
    )

    model.fit(
        train_features
    )

    training_time_seconds = (
        time.time() - training_started_at
    )

    # prediction timing is measured only on the test set
    test_features = scaler.transform(
        test_dataframe[FEATURE_COLUMNS]
    )

    prediction_started_at = time.time()

    model.decision_function(
        test_features
    )

    prediction_time_seconds = (
        time.time() - prediction_started_at
    )

    # full predictions are stored for the application
    all_features = scaler.transform(
        model_dataframe[FEATURE_COLUMNS]
    )

    raw_scores = model.decision_function(
        all_features
    )

    anomaly_scores = -raw_scores

    predicted_anomaly = (
        anomaly_scores > 0
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

    print(
        f"LOF n_neighbors: {N_NEIGHBORS}"
    )

    print(
        "LOF decision rule: anomaly_score > 0"
    )

    print(
        "LOF uses the native learned decision boundary"
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


def train_lof_for_active_dataset() -> Dict[str, float]:

    dataset_id = get_active_dataset_id()

    feature_dataframe = load_feature_measurements(
        dataset_id
    )

    result_dataframe, timing = train_lof(
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
    train_lof_for_active_dataset()


if __name__ == "__main__":
    main()