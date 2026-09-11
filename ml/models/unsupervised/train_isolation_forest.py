"""
isolation forest anomaly detection model

this model isolates unusual records by using random splits in the feature space
records that are isolated quickly are treated as more anomalous
"""

from pathlib import Path
import sys
import time
from typing import Dict, Tuple

import pandas as pd
from sklearn.ensemble import IsolationForest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = PROJECT_ROOT / "ml" / "scripts"

for import_path in (PROJECT_ROOT, SCRIPTS_DIR):
    if str(import_path) not in sys.path:
        sys.path.append(str(import_path))


from ml.models.model_training_utils import (
    FEATURE_COLUMNS,
    RANDOM_STATE,
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


MODEL_NAME = "Isolation Forest"

# expected proportion of anomalous training records
# this value is fixed before evaluation and does not use test labels
CONTAMINATION = 0.03


def train_isolation_forest(
    dataframe: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[str, float]]:

    # convert model features to numeric values
    model_dataframe = convert_feature_columns_to_numeric(
        dataframe
    )

    # split records chronologically
    train_raw, test_raw = chronological_train_test_split(
        model_dataframe
    )

    # remember the exact train and test measurement ids
    train_ids = set(
        train_raw["id"].astype(int).tolist()
    )

    test_ids = set(
        test_raw["id"].astype(int).tolist()
    )

    # fill train and test using medians learned only from train
    train_dataframe, test_dataframe = (
        fill_missing_features_from_train(
            train_raw,
            test_raw,
        )
    )

    # prepare the full dataset using the same training data
    _, full_dataframe = fill_missing_features_from_train(
        train_raw,
        model_dataframe,
    )

    training_started_at = time.time()

    # isolation forest does not require feature scaling
    train_features = train_dataframe[FEATURE_COLUMNS]

    model = IsolationForest(
        n_estimators=200,
        contamination=CONTAMINATION,
        random_state=RANDOM_STATE,
    )

    # train only on the chronological training part
    model.fit(
        train_features
    )

    training_time_seconds = (
        time.time() - training_started_at
    )

    # measure prediction time only on the test set
    prediction_started_at = time.time()

    test_features = test_dataframe[FEATURE_COLUMNS]

    model.predict(
        test_features
    )

    model.decision_function(
        test_features
    )

    prediction_time_seconds = (
        time.time() - prediction_started_at
    )

    # full predictions are stored for the application
    full_features = full_dataframe[FEATURE_COLUMNS]

    predictions = model.predict(
        full_features
    )

    # sklearn gives larger decision values to more normal records
    raw_scores = model.decision_function(
        full_features
    )

    # invert scores so larger values represent stronger anomalies
    anomaly_scores = -raw_scores

    results = add_result_columns(
        dataframe=full_dataframe,
        predicted_anomaly=predictions == -1,
        anomaly_scores=anomaly_scores,
    )

    # store the exact split membership for later evaluation
    results["evaluation_split"] = results["id"].apply(
        lambda measurement_id: (
            "train"
            if int(measurement_id) in train_ids
            else "test"
            if int(measurement_id) in test_ids
            else "full"
        )
    )

    print(
        f"Isolation Forest contamination: "
        f"{CONTAMINATION}"
    )

    print(
        f"Train rows: "
        f"{len(train_dataframe)}"
    )

    print(
        f"Test rows: "
        f"{len(test_dataframe)}"
    )

    return (
        results,
        build_timing(
            training_time_seconds,
            prediction_time_seconds,
        ),
    )


def train_model_for_active_dataset() -> Dict[str, float]:
    dataset_id = get_active_dataset_id()

    feature_dataframe = load_feature_measurements(
        dataset_id
    )

    result_dataframe, timing = train_isolation_forest(
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
    train_model_for_active_dataset()


if __name__ == "__main__":
    main()