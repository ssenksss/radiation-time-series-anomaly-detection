"""
ecod anomaly detection model

this model checks how extreme a record is in the empirical feature distributions
records that fall in distribution tails receive higher anomaly scores
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

from pyod.models.ecod import ECOD

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


MODEL_NAME = "ECOD"

IQR_MULTIPLIER = 1.5


def train_ecod(
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

    train_features = train_dataframe[
        FEATURE_COLUMNS
    ].to_numpy()

    test_features = test_dataframe[
        FEATURE_COLUMNS
    ].to_numpy()

    all_features = model_dataframe[
        FEATURE_COLUMNS
    ].to_numpy()

    training_started_at = time.time()

    model = ECOD(
        contamination=0.1,
    )

    model.fit(
        train_features
    )

    train_anomaly_scores = model.decision_function(
        train_features
    )

    q1 = np.percentile(
        train_anomaly_scores,
        25,
    )

    q3 = np.percentile(
        train_anomaly_scores,
        75,
    )

    iqr = q3 - q1

    anomaly_cutoff = (
        q3
        + IQR_MULTIPLIER
        * iqr
    )

    training_time_seconds = (
        time.time() - training_started_at
    )

    # prediction timing is measured only on the test set
    prediction_started_at = time.time()

    test_anomaly_scores = model.decision_function(
        test_features
    )

    test_anomaly_scores > anomaly_cutoff

    prediction_time_seconds = (
        time.time() - prediction_started_at
    )

    # full scores are stored for the application
    anomaly_scores = model.decision_function(
        all_features
    )

    predicted_anomaly = (
        anomaly_scores > anomaly_cutoff
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
        f"ECOD train Q1: {q1}"
    )

    print(
        f"ECOD train Q3: {q3}"
    )

    print(
        f"ECOD train IQR: {iqr}"
    )

    print(
        f"ECOD IQR multiplier: {IQR_MULTIPLIER}"
    )

    print(
        f"ECOD anomaly score cutoff: {anomaly_cutoff}"
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


def train_ecod_for_active_dataset() -> Dict[str, float]:

    dataset_id = get_active_dataset_id()

    feature_dataframe = load_feature_measurements(
        dataset_id
    )

    result_dataframe, timing = train_ecod(
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
    train_ecod_for_active_dataset()


if __name__ == "__main__":
    main()