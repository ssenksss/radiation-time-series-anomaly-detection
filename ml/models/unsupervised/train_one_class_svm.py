"""
one-class svm anomaly detection model

this model learns the boundary of normal measurements without using labels
records outside that boundary are marked as possible anomalies
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
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

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


MODEL_NAME = "One-Class SVM"


def train_one_class_svm(dataframe: pd.DataFrame, threshold: float) -> Tuple[pd.DataFrame, Dict[str, float]]:
    model_dataframe = safe_fill_feature_columns(dataframe)
    train_dataframe, test_dataframe = chronological_train_test_split(model_dataframe)

    contamination = calculate_contamination_from_threshold(train_dataframe, threshold)

    training_started_at = time.time()

    scaler = StandardScaler()
    train_features = scaler.fit_transform(train_dataframe[FEATURE_COLUMNS])
    all_features = scaler.transform(model_dataframe[FEATURE_COLUMNS])

    model = OneClassSVM(
        kernel="rbf",
        gamma="scale",
        nu=contamination,
    )
    model.fit(train_features)

    training_time_seconds = time.time() - training_started_at

    prediction_started_at = time.time()
    predictions = model.predict(all_features)
    anomaly_scores = -model.decision_function(all_features)
    prediction_time_seconds = time.time() - prediction_started_at

    results = add_result_columns(
        dataframe=model_dataframe,
        predicted_anomaly=predictions == -1,
        anomaly_scores=anomaly_scores,
        threshold=threshold,
    )

    print(f"Threshold used for One-Class SVM sensitivity: {threshold}")
    print(f"Calculated contamination / nu: {contamination}")
    print(f"Train rows: {len(train_dataframe)}")
    print(f"Test rows: {len(test_dataframe)}")

    return results, build_timing(training_time_seconds, prediction_time_seconds)


def train_one_class_svm_for_active_dataset() -> Dict[str, float]:
    dataset_id = get_active_dataset_id()
    threshold = get_threshold()

    feature_dataframe = load_feature_measurements(dataset_id)
    result_dataframe, timing = train_one_class_svm(feature_dataframe, threshold)
    replace_anomaly_results(dataset_id, MODEL_NAME, result_dataframe)
    mark_dataset_as_model_trained(dataset_id)

    print_training_summary(MODEL_NAME, dataset_id, result_dataframe)

    return timing


def main():
    train_one_class_svm_for_active_dataset()


if __name__ == "__main__":
    main()
