from pathlib import Path
import hashlib
import sys
import time
from typing import Any, Callable, Dict, Optional, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "ml" / "scripts"

for import_path in (PROJECT_ROOT, SCRIPTS_DIR):
    if str(import_path) not in sys.path:
        sys.path.append(str(import_path))

import numpy as np
import pandas as pd
from sklearn.metrics import (
    auc,
    f1_score,
    precision_recall_curve,
    roc_auc_score,
)

from db import fetch_one, fetch_all, execute_query, execute_many

from ml.models.supervised.train_logistic_regression import (
    MODEL_NAME as LOGISTIC_REGRESSION_NAME,
    MODEL_ID as LOGISTIC_REGRESSION_ID,
    train_supervised_model as train_logistic_regression_model,
)

from ml.models.supervised.train_decision_tree import (
    MODEL_NAME as DECISION_TREE_NAME,
    MODEL_ID as DECISION_TREE_ID,
    train_supervised_model as train_decision_tree_model,
)

from ml.models.supervised.train_random_forest import (
    MODEL_NAME as RANDOM_FOREST_NAME,
    MODEL_ID as RANDOM_FOREST_ID,
    train_supervised_model as train_random_forest_model,
)

from ml.models.supervised.train_gradient_boosting import (
    MODEL_NAME as GRADIENT_BOOSTING_NAME,
    MODEL_ID as GRADIENT_BOOSTING_ID,
    train_supervised_model as train_gradient_boosting_model,
)

from ml.models.supervised.train_knn_classifier import (
    MODEL_NAME as KNN_CLASSIFIER_NAME,
    MODEL_ID as KNN_CLASSIFIER_ID,
    train_supervised_model as train_knn_classifier_model,
)


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

TRAIN_RATIO = 0.70


SupervisedTrainFunction = Callable[
    [
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        list[str],
    ],
    Dict[str, Any],
]


SUPERVISED_MODELS: list[
    tuple[
        str,
        str,
        SupervisedTrainFunction,
    ]
] = [
    (
        LOGISTIC_REGRESSION_NAME,
        LOGISTIC_REGRESSION_ID,
        train_logistic_regression_model,
    ),
    (
        DECISION_TREE_NAME,
        DECISION_TREE_ID,
        train_decision_tree_model,
    ),
    (
        RANDOM_FOREST_NAME,
        RANDOM_FOREST_ID,
        train_random_forest_model,
    ),
    (
        GRADIENT_BOOSTING_NAME,
        GRADIENT_BOOSTING_ID,
        train_gradient_boosting_model,
    ),
    (
        KNN_CLASSIFIER_NAME,
        KNN_CLASSIFIER_ID,
        train_knn_classifier_model,
    ),
]


def get_active_dataset_id() -> int:
    row = fetch_one(
        """
        SELECT value
        FROM app_settings
        WHERE key = 'active_dataset_id';
        """
    )

    if not row:
        raise RuntimeError(
            "No active_dataset_id found in app_settings."
        )

    return int(row["value"])




def load_labeled_feature_measurements(
    dataset_id: int,
) -> pd.DataFrame:
    # load all records so the time boundary matches the unsupervised pipeline
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
        ORDER BY fm.timestamp;
        """,
        (dataset_id,),
    )

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        raise RuntimeError(
            "No labeled feature measurements found. "
            "Dataset must contain is_anomaly."
        )

    dataframe["timestamp"] = pd.to_datetime(
        dataframe["timestamp"]
    )

    for column in FEATURE_COLUMNS:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

    dataframe["original_label"] = dataframe["original_label"].map(
        lambda value: int(value) if pd.notna(value) else np.nan
    )

    labeled_values = dataframe["original_label"].dropna()

    if labeled_values.empty:
        raise RuntimeError(
            "No labeled feature measurements found. "
            "Dataset must contain is_anomaly."
        )

    if (
        len(
            np.unique(
                labeled_values
            )
        )
        < 2
    ):
        raise RuntimeError(
            "Supervised training requires both normal "
            "and anomaly examples."
        )

    return dataframe.reset_index(
        drop=True
    )


def chronological_split(
    dataframe: pd.DataFrame,
) -> Tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.Series,
]:
    # preserve natural time order
    sorted_dataframe = (
        dataframe
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    split_index = int(
        len(sorted_dataframe)
        * TRAIN_RATIO
    )

    train_period = (
        sorted_dataframe
        .iloc[:split_index]
        .copy()
    )

    test_period = (
        sorted_dataframe
        .iloc[split_index:]
        .copy()
    )

    if (
        train_period.empty
        or test_period.empty
    ):
        raise RuntimeError(
            "Train/test split failed because dataset is too small."
        )

    # supervised fitting and evaluation use only known labels inside each period
    train_dataframe = train_period.dropna(
        subset=["original_label"]
    ).copy()

    test_dataframe = test_period.dropna(
        subset=["original_label"]
    ).copy()

    if train_dataframe.empty:
        raise RuntimeError(
            "No labeled records found in the chronological training period."
        )

    if test_dataframe.empty:
        raise RuntimeError(
            "No labeled records found in the chronological test period."
        )

    train_dataframe["original_label"] = train_dataframe["original_label"].astype(int)
    test_dataframe["original_label"] = test_dataframe["original_label"].astype(int)

    if (
        len(
            np.unique(
                train_dataframe[
                    "original_label"
                ]
            )
        )
        < 2
    ):
        raise RuntimeError(
            "The chronological train split contains only one class. "
            "Use a labeled dataset where anomalies exist "
            "in the training period."
        )

    if (
        len(
            np.unique(
                test_dataframe[
                    "original_label"
                ]
            )
        )
        < 2
    ):
        print(
            "Warning: chronological test split contains only one class. "
            "Metrics may be less informative."
        )

    # calculate missing-value replacement only from train data
    train_medians = (
        train_dataframe[
            FEATURE_COLUMNS
        ]
        .median(
            numeric_only=True
        )
    )

    train_dataframe[
        FEATURE_COLUMNS
    ] = (
        train_dataframe[
            FEATURE_COLUMNS
        ]
        .fillna(
            train_medians
        )
        .fillna(0)
    )

    test_dataframe[
        FEATURE_COLUMNS
    ] = (
        test_dataframe[
            FEATURE_COLUMNS
        ]
        .fillna(
            train_medians
        )
        .fillna(0)
    )

    return (
        train_dataframe,
        test_dataframe,
        train_medians,
        )


def prepare_full_dataframe(
    dataframe: pd.DataFrame,
    train_medians: pd.Series,
) -> pd.DataFrame:
    # prepare all records for application predictions
    # missing values are replaced only with values learned from train data
    prepared_dataframe = dataframe.copy()

    prepared_dataframe[FEATURE_COLUMNS] = (
        prepared_dataframe[FEATURE_COLUMNS]
        .fillna(train_medians)
        .fillna(0)
    )

    return prepared_dataframe


def validate_chronological_split(
    train_dataframe: pd.DataFrame,
    test_dataframe: pd.DataFrame,
) -> None:
    train_ids = set(
        train_dataframe[
            "id"
        ].astype(int)
    )

    test_ids = set(
        test_dataframe[
            "id"
        ].astype(int)
    )

    overlapping_ids = (
        train_ids
        .intersection(
            test_ids
        )
    )

    train_max_timestamp = (
        train_dataframe[
            "timestamp"
        ].max()
    )

    test_min_timestamp = (
        test_dataframe[
            "timestamp"
        ].min()
    )

    chronological_order_valid = (
        train_max_timestamp
        <= test_min_timestamp
    )

    print(
        "\nChronological split check:"
    )

    print(
        f"Train ID count: "
        f"{len(train_ids)}"
    )

    print(
        f"Test ID count: "
        f"{len(test_ids)}"
    )

    print(
        f"Overlapping IDs: "
        f"{len(overlapping_ids)}"
    )

    print(
        f"Last train timestamp: "
        f"{train_max_timestamp}"
    )

    print(
        f"First test timestamp: "
        f"{test_min_timestamp}"
    )

    print(
        f"Chronological order valid: "
        f"{chronological_order_valid}"
    )

    if overlapping_ids:
        raise RuntimeError(
            "Data leakage detected: train and test "
            "contain the same measurement IDs."
        )

    if not chronological_order_valid:
        raise RuntimeError(
            "Chronological split is invalid: "
            "test data begins before training data ends."
        )





def normalize_scores(
    scores: np.ndarray,
) -> np.ndarray:
    values = np.asarray(
        scores,
        dtype=float,
    )

    min_value = float(
        values.min()
    )

    max_value = float(
        values.max()
    )

    if max_value == min_value:
        return np.zeros_like(
            values
        )

    return (
        values - min_value
    ) / (
        max_value - min_value
    )


def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_score: np.ndarray,
) -> Dict[str, float]:
    y_true = np.asarray(
        y_true
    ).astype(int)

    y_pred = np.asarray(
        y_pred
    ).astype(int)

    y_score = np.asarray(
        y_score
    ).astype(float)

    tp = int(
        (
            (y_true == 1)
            & (y_pred == 1)
        ).sum()
    )

    tn = int(
        (
            (y_true == 0)
            & (y_pred == 0)
        ).sum()
    )

    fp = int(
        (
            (y_true == 0)
            & (y_pred == 1)
        ).sum()
    )

    fn = int(
        (
            (y_true == 1)
            & (y_pred == 0)
        ).sum()
    )

    total = (
        tp
        + tn
        + fp
        + fn
    )

    accuracy = (
        (
            (tp + tn)
            / total
        )
        * 100
        if total
        else 0
    )

    precision = (
        tp
        / (tp + fp)
        if (tp + fp)
        else 0
    )

    recall = (
        tp
        / (tp + fn)
        if (tp + fn)
        else 0
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    fpr = (
        fp
        / (fp + tn)
        if (fp + tn)
        else 0
    )

    fnr = (
        fn
        / (fn + tp)
        if (fn + tp)
        else 0
    )

    has_both_classes = (
        len(
            np.unique(
                y_true
            )
        )
        == 2
    )

    roc_auc = None
    pr_auc = None

    if has_both_classes:
        roc_auc = roc_auc_score(
            y_true,
            y_score,
        )

        precision_curve, recall_curve, _ = precision_recall_curve(
            y_true,
            y_score,
        )

        pr_auc = auc(
            recall_curve[::-1],
            precision_curve[::-1],
        )

    return {
        "evaluation_mode": "supervised",
        "accuracy": round(
            float(accuracy),
            2,
        ),
        "precision": round(
            float(precision),
            4,
        ),
        "recall": round(
            float(recall),
            4,
        ),
        "f1_score": round(
            float(f1),
            4,
        ),
        "roc_auc": (
            round(
                float(roc_auc),
                4,
            )
            if roc_auc is not None
            else None
        ),
        "pr_auc": (
            round(
                float(pr_auc),
                4,
            )
            if pr_auc is not None
            else None
        ),
        "fpr": round(
            float(fpr),
            4,
        ),
        "fnr": round(
            float(fnr),
            4,
        ),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "true_anomalies": int(
            y_true.sum()
        ),
        "total_records": total,
        "total_anomalies": int(
            y_pred.sum()
        ),
        "score_mean": round(
            float(
                y_score.mean()
            ),
            6,
        ),
        "score_std": round(
            float(
                y_score.std()
            ),
            6,
        ),
        "score_variance": round(
            float(
                y_score.var()
            ),
            6,
        ),
    }


def array_hash(
    values: np.ndarray,
) -> str:
    array = np.ascontiguousarray(
        np.asarray(
            values
        )
    )

    return hashlib.sha256(
        array.tobytes()
    ).hexdigest()[:16]


def print_score_audit(
    model_name: str,
    y_test: np.ndarray,
    y_score: np.ndarray,
) -> None:
    print(
        "\nScore audit:"
    )

    print(
        f"Model: "
        f"{model_name}"
    )

    print(
        f"y_test hash: "
        f"{array_hash(y_test)}"
    )

    print(
        f"y_score hash: "
        f"{array_hash(y_score)}"
    )

    print(
        f"Score count: "
        f"{len(y_score)}"
    )

    print(
        f"Unique score values: "
        f"{len(np.unique(y_score))}"
    )

    print(
        f"Score min: "
        f"{float(np.min(y_score)):.8f}"
    )

    print(
        f"Score max: "
        f"{float(np.max(y_score)):.8f}"
    )

    print(
        f"Score mean: "
        f"{float(np.mean(y_score)):.8f}"
    )


def compare_model_scores(
    model_scores: Dict[
        str,
        np.ndarray,
    ],
) -> None:
    model_names = list(
        model_scores.keys()
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "SUPERVISED SCORE COMPARISON"
    )

    print(
        "=" * 60
    )

    for first_index in range(
        len(model_names)
    ):
        for second_index in range(
            first_index + 1,
            len(model_names),
        ):
            first_name = (
                model_names[
                    first_index
                ]
            )

            second_name = (
                model_names[
                    second_index
                ]
            )

            first_scores = (
                model_scores[
                    first_name
                ]
            )

            second_scores = (
                model_scores[
                    second_name
                ]
            )

            same_length = (
                len(first_scores)
                == len(second_scores)
            )

            identical = (
                same_length
                and np.array_equal(
                    first_scores,
                    second_scores,
                )
            )

            approximately_equal = (
                same_length
                and np.allclose(
                    first_scores,
                    second_scores,
                    rtol=1e-12,
                    atol=1e-12,
                )
            )

            print(
                f"{first_name} vs "
                f"{second_name}: "
                f"identical={identical}, "
                f"allclose={approximately_equal}"
            )


def print_perfect_pr_auc_audit(
    model_name: str,
    y_test: np.ndarray,
    y_score: np.ndarray,
    pr_auc: Optional[float],
) -> None:
    if (
        pr_auc is None
        or pr_auc < 1.0
    ):
        return

    positive_scores = (
        y_score[
            y_test == 1
        ]
    )

    negative_scores = (
        y_score[
            y_test == 0
        ]
    )

    if (
        len(positive_scores) == 0
        or len(negative_scores) == 0
    ):
        return

    min_positive = float(
        positive_scores.min()
    )

    max_negative = float(
        negative_scores.max()
    )

    perfect_ranking = (
        min_positive
        > max_negative
    )

    print(
        "\nPerfect PR-AUC audit:"
    )

    print(
        f"Model: "
        f"{model_name}"
    )

    print(
        f"Positive scores: "
        f"{len(positive_scores)}"
    )

    print(
        f"Negative scores: "
        f"{len(negative_scores)}"
    )

    print(
        f"Minimum positive score: "
        f"{min_positive:.8f}"
    )

    print(
        f"Maximum negative score: "
        f"{max_negative:.8f}"
    )

    print(
        f"All positive samples ranked above "
        f"all negative samples: "
        f"{perfect_ranking}"
    )


def train_predict_model(
    train_function: SupervisedTrainFunction,
    train_dataframe: pd.DataFrame,
    test_dataframe: pd.DataFrame,
    full_dataframe: pd.DataFrame,
) -> Tuple[
    pd.DataFrame,
    Dict[str, float],
    np.ndarray,
    np.ndarray,
]:
    output = train_function(
        train_dataframe,
        test_dataframe,
        full_dataframe,
        FEATURE_COLUMNS,
    )

    y_test = (
        test_dataframe[
            "original_label"
        ]
        .astype(int)
        .to_numpy()
        .copy()
    )

    test_predictions = (
        np.asarray(
            output[
                "test_predictions"
            ]
        )
        .astype(int)
        .copy()
    )

    test_scores = (
        np.asarray(
            output[
                "test_scores"
            ]
        )
        .astype(float)
        .copy()
    )

    if (
        len(y_test)
        != len(
            test_predictions
        )
    ):
        raise RuntimeError(
            "Prediction length does not match y_test length."
        )

    if (
        len(y_test)
        != len(
            test_scores
        )
    ):
        raise RuntimeError(
            "Score length does not match y_test length."
        )

    metrics = calculate_metrics(
        y_test,
        test_predictions,
        test_scores,
    )

    metrics[
        "training_time_seconds"
    ] = output[
        "training_time_seconds"
    ]

    metrics[
        "prediction_time_seconds"
    ] = output[
        "prediction_time_seconds"
    ]

    results = (
        full_dataframe.copy()
    )

    results[
        "predicted_anomaly"
    ] = (
        np.asarray(
            output[
                "full_predictions"
            ]
        )
        .astype(bool)
    )

    results[
        "anomaly_score"
    ] = normalize_scores(
        np.asarray(
            output[
                "full_scores"
            ]
        )
        .astype(float)
    )

    ordered_full_dataframe = full_dataframe.sort_values(
        "timestamp"
    ).reset_index(drop=True)

    split_index = int(
        len(ordered_full_dataframe) * TRAIN_RATIO
    )

    train_ids = set(
        ordered_full_dataframe.iloc[:split_index]["id"].astype(int)
    )

    test_ids = set(
        ordered_full_dataframe.iloc[split_index:]["id"].astype(int)
    )

    results[
        "evaluation_split"
    ] = results[
        "id"
    ].astype(int).apply(
        lambda measurement_id: (
            "train"
            if measurement_id in train_ids
            else "test"
            if measurement_id in test_ids
            else None
        )
    )

    if results[
        "evaluation_split"
    ].isna().any():
        raise RuntimeError(
            "Some prediction rows could not be assigned "
            "to train or test split."
        )

    return (
        results,
        metrics,
        y_test,
        test_scores,
    )


def replace_anomaly_results(
    dataset_id: int,
    model_name: str,
    results: pd.DataFrame,
) -> None:
    execute_query(
        """
        DELETE FROM anomaly_results
        WHERE dataset_id = %s
          AND model_name = %s;
        """,
        (
            dataset_id,
            model_name,
        ),
    )

    rows = []

    for _, item in (
        results.iterrows()
    ):
        radiation_level = float(
            item[
                "radiation_level"
            ]
        )

        predicted_anomaly = bool(
            item[
                "predicted_anomaly"
            ]
        )

        rows.append(
            (
                dataset_id,
                int(item["id"]),
                item["timestamp"].to_pydatetime(),
                radiation_level,
                predicted_anomaly,
                float(item["anomaly_score"]),
                model_name,
                item["evaluation_split"],
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
            model_name,
            evaluation_split
        )
        VALUES (
            %s, %s, %s, %s,
            %s, %s, %s, %s
        );
        """,
        rows,
    )

def replace_model_metrics(
    dataset_id: int,
    model_name: str,
    metrics: Dict[
        str,
        float,
    ],
) -> None:
    execute_query(
        """
        DELETE FROM model_metrics
        WHERE dataset_id = %s
          AND model_name = %s;
        """,
        (
            dataset_id,
            model_name,
        ),
    )

    execute_query(
        """
        INSERT INTO model_metrics (
            dataset_id,
            model_name,
            accuracy,
            precision_score,
            recall_score,
            f1_score,
            roc_auc,
            pr_auc,
            fpr,
            fnr,
            tp,
            tn,
            fp,
            fn,
            true_anomalies,
            total_records,
            total_anomalies,
            score_mean,
            score_std,
            score_variance,
            training_time_seconds,
            prediction_time_seconds,
            evaluation_mode
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s
        );
        """,
        (
            dataset_id,
            model_name,
            metrics.get(
                "accuracy"
            ),
            metrics.get(
                "precision"
            ),
            metrics.get(
                "recall"
            ),
            metrics.get(
                "f1_score"
            ),
            metrics.get(
                "roc_auc"
            ),
            metrics.get(
                "pr_auc"
            ),
            metrics.get(
                "fpr"
            ),
            metrics.get(
                "fnr"
            ),
            metrics.get(
                "tp"
            ),
            metrics.get(
                "tn"
            ),
            metrics.get(
                "fp"
            ),
            metrics.get(
                "fn"
            ),
            metrics.get(
                "true_anomalies"
            ),
            int(
                metrics.get(
                    "total_records"
                )
                or 0
            ),
            int(
                metrics.get(
                    "total_anomalies"
                )
                or 0
            ),
            metrics.get(
                "score_mean"
            ),
            metrics.get(
                "score_std"
            ),
            metrics.get(
                "score_variance"
            ),
            metrics.get(
                "training_time_seconds"
            ),
            metrics.get(
                "prediction_time_seconds"
            ),
            metrics.get(
                "evaluation_mode"
            ),
        ),
    )


def run_supervised_pipeline() -> None:
    started_at = time.time()

    dataset_id = (
        get_active_dataset_id()
    )

    print(
        "=" * 60
    )

    print(
        "Radiation Monitoring "
        "Supervised ML Pipeline"
    )

    print(
        "Mode: CHRONOLOGICAL TRAIN/TEST"
    )

    print(
        "=" * 60
    )

    print(
        f"Dataset ID: "
        f"{dataset_id}"
    )

    full_dataframe = (
        load_labeled_feature_measurements(
            dataset_id
        )
    )

    (
        train_dataframe,
        test_dataframe,
        train_medians,
    ) = chronological_split(
        full_dataframe
    )

    validate_chronological_split(
        train_dataframe,
        test_dataframe,
    )

    prepared_full_dataframe = (
    prepare_full_dataframe(
        full_dataframe,
        train_medians,
        )
    )

    reference_y_test = (
        test_dataframe[
            "original_label"
        ]
        .astype(int)
        .to_numpy()
        .copy()
    )

    reference_y_test_hash = (
        array_hash(
            reference_y_test
        )
    )

    print(
        f"\nReference y_test hash: "
        f"{reference_y_test_hash}"
    )

    print(
        f"Total records: "
        f"{len(full_dataframe)}"
    )

    print(
        f"Train records: "
        f"{len(train_dataframe)}"
    )

    print(
        f"Test records: "
        f"{len(test_dataframe)}"
    )

    print(
        f"Train anomalies: "
        f"{int(train_dataframe['original_label'].sum())}"
    )

    print(
        f"Test anomalies: "
        f"{int(test_dataframe['original_label'].sum())}"
    )

    model_scores: Dict[
        str,
        np.ndarray,
    ] = {}

    for index, (
        model_name,
        _model_id,
        train_function,
    ) in enumerate(
        SUPERVISED_MODELS,
        start=1,
    ):
        print(
            "\n"
            + "-" * 60
        )

        print(
            f"Step {index}/5: "
            f"train/test "
            f"{model_name}"
        )

        (
            results,
            metrics,
            y_test,
            test_scores,
        ) = train_predict_model(
            train_function=(
                train_function
            ),
            train_dataframe=(
                train_dataframe
            ),
            test_dataframe=(
                test_dataframe
            ),
            full_dataframe=(
                prepared_full_dataframe
            ),
        )

        current_y_test_hash = (
            array_hash(
                y_test
            )
        )

        if (
            current_y_test_hash
            != reference_y_test_hash
        ):
            raise RuntimeError(
                f"{model_name} received "
                f"a different y_test."
            )

        model_scores[
            model_name
        ] = test_scores.copy()

        print_score_audit(
            model_name,
            y_test,
            test_scores,
        )

        print_perfect_pr_auc_audit(
            model_name,
            y_test,
            test_scores,
            metrics.get(
                "pr_auc"
            ),
        )

        replace_anomaly_results(
            dataset_id,
            model_name,
            results,
        )

        replace_model_metrics(
            dataset_id,
            model_name,
            metrics,
        )

        print(
            f"\nAccuracy: "
            f"{metrics['accuracy']}%"
        )

        print(
            f"Precision: "
            f"{metrics['precision']}"
        )

        print(
            f"Recall: "
            f"{metrics['recall']}"
        )

        print(
            f"F1-score: "
            f"{metrics['f1_score']}"
        )

        print(
            f"ROC-AUC: "
            f"{metrics['roc_auc']}"
        )

        print(
            f"PR-AUC: "
            f"{metrics['pr_auc']}"
        )

        print(
            f"FPR: "
            f"{metrics['fpr']}"
        )

        print(
            f"FNR: "
            f"{metrics['fnr']}"
        )

        print(
            "Confusion matrix on TEST: "
            f"TP={metrics['tp']}, "
            f"TN={metrics['tn']}, "
            f"FP={metrics['fp']}, "
            f"FN={metrics['fn']}"
        )

        print(
            f"Training time: "
            f"{metrics['training_time_seconds']} "
            f"seconds"
        )

        print(
            f"Prediction time: "
            f"{metrics['prediction_time_seconds']} "
            f"seconds"
        )

    compare_model_scores(
        model_scores
    )

    elapsed = round(
        time.time()
        - started_at,
        2,
    )

    print(
        "\n"
        + "=" * 60
    )

    print(
        "Supervised pipeline "
        "completed successfully."
    )

    print(
        "All models used the same "
        "chronological test split."
    )

    print(
        "Metrics are based on "
        "test data only."
    )

    print(
        f"Execution time: "
        f"{elapsed} seconds"
    )

    print(
        "=" * 60
    )


def main():
    run_supervised_pipeline()


if __name__ == "__main__":
    main()
