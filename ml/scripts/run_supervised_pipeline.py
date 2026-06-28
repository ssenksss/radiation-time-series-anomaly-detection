import time
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from db import fetch_one, fetch_all, execute_query, execute_many


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
RANDOM_STATE = 42

SUPERVISED_MODELS = {
    "Logistic Regression": "logistic_regression",
    "Decision Tree": "decision_tree",
    "Random Forest": "random_forest",
    "Gradient Boosting": "gradient_boosting",
    "KNN Classifier": "knn_classifier",
}


def get_active_dataset_id() -> int:
    row = fetch_one("SELECT value FROM app_settings WHERE key = 'active_dataset_id';")

    if not row:
        raise RuntimeError("No active_dataset_id found in app_settings.")

    return int(row["value"])


def get_threshold() -> float:
    row = fetch_one("SELECT value FROM app_settings WHERE key = 'threshold';")
    return float(row["value"]) if row else 0.18


def load_labeled_feature_measurements(dataset_id: int) -> pd.DataFrame:
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
          AND cm.original_label IS NOT NULL
        ORDER BY fm.timestamp;
        """,
        (dataset_id,),
    )

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        raise RuntimeError("No labeled feature measurements found. Dataset must contain is_anomaly.")

    dataframe["timestamp"] = pd.to_datetime(dataframe["timestamp"])

    for column in FEATURE_COLUMNS:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    medians = dataframe[FEATURE_COLUMNS].median(numeric_only=True)
    dataframe[FEATURE_COLUMNS] = dataframe[FEATURE_COLUMNS].fillna(medians).fillna(0)

    dataframe["original_label"] = dataframe["original_label"].astype(bool).astype(int)

    if len(np.unique(dataframe["original_label"])) < 2:
        raise RuntimeError("Supervised training requires both normal and anomaly examples.")

    return dataframe.reset_index(drop=True)


def chronological_split(dataframe: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    sorted_dataframe = dataframe.sort_values("timestamp").reset_index(drop=True)
    split_index = int(len(sorted_dataframe) * TRAIN_RATIO)

    train_dataframe = sorted_dataframe.iloc[:split_index].copy()
    test_dataframe = sorted_dataframe.iloc[split_index:].copy()

    if train_dataframe.empty or test_dataframe.empty:
        raise RuntimeError("Train/test split failed because dataset is too small.")

    if len(np.unique(train_dataframe["original_label"])) < 2:
        raise RuntimeError(
            "The chronological train split contains only one class. "
            "Use a labeled dataset where anomalies exist in the training period."
        )

    if len(np.unique(test_dataframe["original_label"])) < 2:
        print("Warning: chronological test split contains only one class. Metrics may be less informative.")

    return train_dataframe, test_dataframe


def build_status(radiation_level: float, predicted_anomaly: bool, threshold: float) -> str:
    if not predicted_anomaly:
        return "normal"

    if threshold > 0 and radiation_level >= threshold * 2:
        return "critical"

    return "high"


def normalize_scores(scores: np.ndarray) -> np.ndarray:
    values = np.asarray(scores, dtype=float)

    min_value = float(values.min())
    max_value = float(values.max())

    if max_value == min_value:
        return np.zeros_like(values)

    return (values - min_value) / (max_value - min_value)


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)

    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())

    total = tp + tn + fp + fn

    accuracy = ((tp + tn) / total) * 100 if total else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    fpr = fp / (fp + tn) if (fp + tn) else 0
    fnr = fn / (fn + tp) if (fn + tp) else 0

    return {
        "accuracy": round(accuracy, 2),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "fpr": round(fpr, 4),
        "fnr": round(fnr, 4),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "total_records": total,
        "total_anomalies": int(y_pred.sum()),
    }


def build_model(model_name: str):
    if model_name == "Logistic Regression":
        return LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )

    if model_name == "Decision Tree":
        return DecisionTreeClassifier(
            max_depth=5,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )

    if model_name == "Random Forest":
        return RandomForestClassifier(
            n_estimators=150,
            max_depth=7,
            min_samples_leaf=4,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )

    if model_name == "Gradient Boosting":
        return GradientBoostingClassifier(
            n_estimators=80,
            learning_rate=0.04,
            max_depth=2,
            random_state=RANDOM_STATE,
        )

    if model_name == "KNN Classifier":
        return KNeighborsClassifier(
            n_neighbors=9,
            weights="distance",
        )

    raise ValueError(f"Unsupported supervised model: {model_name}")


def model_requires_scaling(model_name: str) -> bool:
    return model_name in {"Logistic Regression", "KNN Classifier"}


def train_predict_model(
        model_name: str,
        train_dataframe: pd.DataFrame,
        test_dataframe: pd.DataFrame,
        full_dataframe: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    model = build_model(model_name)

    x_train = train_dataframe[FEATURE_COLUMNS]
    y_train = train_dataframe["original_label"].astype(int).to_numpy()

    x_test = test_dataframe[FEATURE_COLUMNS]
    y_test = test_dataframe["original_label"].astype(int).to_numpy()

    x_full = full_dataframe[FEATURE_COLUMNS]

    if model_requires_scaling(model_name):
        scaler = StandardScaler()
        x_train_model = scaler.fit_transform(x_train)
        x_test_model = scaler.transform(x_test)
        x_full_model = scaler.transform(x_full)
    else:
        x_train_model = x_train
        x_test_model = x_test
        x_full_model = x_full

    model.fit(x_train_model, y_train)

    test_predictions = model.predict(x_test_model).astype(int)
    full_predictions = model.predict(x_full_model).astype(int)

    if hasattr(model, "predict_proba"):
        full_scores = model.predict_proba(x_full_model)[:, 1]
    elif hasattr(model, "decision_function"):
        full_scores = model.decision_function(x_full_model)
    else:
        full_scores = full_predictions.astype(float)

    metrics = calculate_metrics(y_test, test_predictions)

    results = full_dataframe.copy()
    results["predicted_anomaly"] = full_predictions.astype(bool)
    results["anomaly_score"] = normalize_scores(full_scores)

    return results, metrics


def replace_anomaly_results(
        dataset_id: int,
        model_name: str,
        results: pd.DataFrame,
        threshold: float,
) -> None:
    execute_query(
        """
        DELETE FROM anomaly_results
        WHERE dataset_id = %s
          AND model_name = %s;
        """,
        (dataset_id, model_name),
    )

    rows = []

    for _, item in results.iterrows():
        radiation_level = float(item["radiation_level"])
        predicted_anomaly = bool(item["predicted_anomaly"])

        rows.append(
            (
                dataset_id,
                int(item["id"]),
                item["timestamp"].to_pydatetime(),
                radiation_level,
                predicted_anomaly,
                float(item["anomaly_score"]),
                build_status(radiation_level, predicted_anomaly, threshold),
                model_name,
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
            status,
            model_name
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """,
        rows,
    )


def replace_model_metrics(dataset_id: int, model_name: str, metrics: Dict[str, float]) -> None:
    execute_query(
        """
        DELETE FROM model_metrics
        WHERE dataset_id = %s
          AND model_name = %s;
        """,
        (dataset_id, model_name),
    )

    execute_query(
        """
        INSERT INTO model_metrics (
            dataset_id,
            model_name,
            accuracy,
            precision_score,
            recall_score,
            fpr,
            fnr,
            total_records,
            total_anomalies
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """,
        (
            dataset_id,
            model_name,
            metrics["accuracy"],
            metrics["precision"],
            metrics["recall"],
            metrics["fpr"],
            metrics["fnr"],
            int(metrics["total_records"]),
            int(metrics["total_anomalies"]),
        ),
    )


def run_supervised_pipeline() -> None:
    started_at = time.time()

    dataset_id = get_active_dataset_id()
    threshold = get_threshold()

    print("=" * 60)
    print("Radiation Monitoring Supervised ML Pipeline")
    print("Mode: CHRONOLOGICAL TRAIN/TEST")
    print("=" * 60)
    print(f"Dataset ID: {dataset_id}")

    full_dataframe = load_labeled_feature_measurements(dataset_id)
    train_dataframe, test_dataframe = chronological_split(full_dataframe)

    print(f"Total records: {len(full_dataframe)}")
    print(f"Train records: {len(train_dataframe)}")
    print(f"Test records: {len(test_dataframe)}")
    print(f"Train anomalies: {int(train_dataframe['original_label'].sum())}")
    print(f"Test anomalies: {int(test_dataframe['original_label'].sum())}")

    for index, model_name in enumerate(SUPERVISED_MODELS.keys(), start=1):
        print("\n" + "-" * 60)
        print(f"Step {index}/5: train/test {model_name}")

        results, metrics = train_predict_model(
            model_name=model_name,
            train_dataframe=train_dataframe,
            test_dataframe=test_dataframe,
            full_dataframe=full_dataframe,
        )

        replace_anomaly_results(dataset_id, model_name, results, threshold)
        replace_model_metrics(dataset_id, model_name, metrics)

        print(f"Accuracy: {metrics['accuracy']}%")
        print(f"Precision: {metrics['precision']}")
        print(f"Recall: {metrics['recall']}")
        print(f"FPR: {metrics['fpr']}")
        print(f"FNR: {metrics['fnr']}")
        print(
            f"Confusion matrix on TEST: "
            f"TP={metrics['tp']}, TN={metrics['tn']}, FP={metrics['fp']}, FN={metrics['fn']}"
        )

    elapsed = round(time.time() - started_at, 2)

    print("\n" + "=" * 60)
    print("Supervised pipeline completed successfully.")
    print("Metrics are based on chronological test split only.")
    print(f"Execution time: {elapsed} seconds")
    print("=" * 60)


def main():
    run_supervised_pipeline()


if __name__ == "__main__":
    main()