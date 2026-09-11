"""
gaussian mixture model anomaly detection

the model estimates the probability distribution of normal training data
records with low likelihood receive higher anomaly scores
"""

from pathlib import Path
import sys
import time
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from sklearn.mixture import GaussianMixture
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


MODEL_NAME = "Gaussian Mixture Model"

MIN_COMPONENTS = 1
MAX_COMPONENTS = 5
COVARIANCE_TYPE = "full"
RANDOM_STATE = 42

IQR_MULTIPLIER = 1.5


def select_best_number_of_components(
    train_features,
) -> Tuple[int, Dict[int, float]]:
    bic_scores = {}

    best_n_components = MIN_COMPONENTS
    best_bic = float("inf")

    for n_components in range(
        MIN_COMPONENTS,
        MAX_COMPONENTS + 1,
    ):
        candidate_model = GaussianMixture(
            n_components=n_components,
            covariance_type=COVARIANCE_TYPE,
            random_state=RANDOM_STATE,
        )

        candidate_model.fit(
            train_features
        )

        bic_value = candidate_model.bic(
            train_features
        )

        bic_scores[n_components] = bic_value

        if bic_value < best_bic:
            best_bic = bic_value
            best_n_components = n_components

    return best_n_components, bic_scores


def train_gmm(
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

    scaler = StandardScaler()

    train_features = scaler.fit_transform(
        train_dataframe[FEATURE_COLUMNS]
    )

    test_features = scaler.transform(
        test_dataframe[FEATURE_COLUMNS]
    )

    all_features = scaler.transform(
        model_dataframe[FEATURE_COLUMNS]
    )

    training_started_at = time.time()

    best_n_components, bic_scores = select_best_number_of_components(
        train_features
    )

    model = GaussianMixture(
        n_components=best_n_components,
        covariance_type=COVARIANCE_TYPE,
        random_state=RANDOM_STATE,
    )

    model.fit(
        train_features
    )

    train_log_likelihood = model.score_samples(
        train_features
    )

    train_anomaly_scores = (
        -train_log_likelihood
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

    test_log_likelihood = model.score_samples(
        test_features
    )

    test_anomaly_scores = (
        -test_log_likelihood
    )

    test_anomaly_scores > anomaly_cutoff

    prediction_time_seconds = (
        time.time() - prediction_started_at
    )

    # full scores are stored for the application
    log_likelihood = model.score_samples(
        all_features
    )

    anomaly_scores = (
        -log_likelihood
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
        "GMM BIC values:"
    )

    for n_components, bic_value in bic_scores.items():
        print(
            f"  {n_components} components: {bic_value}"
        )

    print(
        f"GMM selected components: {best_n_components}"
    )

    print(
        f"GMM covariance type: {COVARIANCE_TYPE}"
    )

    print(
        f"GMM train Q1: {q1}"
    )

    print(
        f"GMM train Q3: {q3}"
    )

    print(
        f"GMM train IQR: {iqr}"
    )

    print(
        f"GMM IQR multiplier: {IQR_MULTIPLIER}"
    )

    print(
        f"GMM anomaly score cutoff: {anomaly_cutoff}"
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


def train_gaussian_mixture_for_active_dataset() -> Dict[str, float]:
    dataset_id = get_active_dataset_id()

    feature_dataframe = load_feature_measurements(
        dataset_id
    )

    result_dataframe, timing = train_gmm(
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
    train_gaussian_mixture_for_active_dataset()


if __name__ == "__main__":
    main()