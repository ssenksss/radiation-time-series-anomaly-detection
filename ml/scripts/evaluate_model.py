from typing import Optional, Sequence

import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix

from db import fetch_one, fetch_all, execute_query


def get_active_dataset_id() -> int:
    row = fetch_one(
        """
        SELECT value
        FROM app_settings
        WHERE key = 'active_dataset_id';
        """
    )

    if not row:
        raise RuntimeError("No active_dataset_id found in app_settings.")

    return int(row["value"])


def get_model_names_for_dataset(dataset_id: int) -> list:
    rows = fetch_all(
        """
        SELECT DISTINCT model_name
        FROM anomaly_results
        WHERE dataset_id = %s
        ORDER BY model_name;
        """,
        (dataset_id,),
    )

    return [row["model_name"] for row in rows]


def load_evaluation_data(dataset_id: int, model_name: str) -> pd.DataFrame:
    rows = fetch_all(
        """
        SELECT
            ar.predicted_anomaly,
            ar.anomaly_score,
            cm.original_label
        FROM anomaly_results ar
        JOIN feature_measurements fm
            ON ar.feature_measurement_id = fm.id
        JOIN clean_measurements cm
            ON fm.clean_measurement_id = cm.id
        WHERE ar.dataset_id = %s
          AND ar.model_name = %s
          AND cm.original_label IS NOT NULL
        ORDER BY ar.timestamp;
        """,
        (dataset_id, model_name),
    )

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        raise RuntimeError(
            f"No evaluation labels found for model '{model_name}'. "
            "The dataset must contain original is_anomaly labels."
        )

    return dataframe


def calculate_metrics(dataframe: pd.DataFrame) -> dict:
    y_true = dataframe["original_label"].astype(bool)
    y_pred = dataframe["predicted_anomaly"].astype(bool)

    accuracy = accuracy_score(y_true, y_pred) * 100
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        y_pred,
        labels=[False, True],
    ).ravel()

    fpr = fp / (fp + tn) if (fp + tn) else 0
    fnr = fn / (fn + tp) if (fn + tp) else 0

    return {
        "accuracy": round(float(accuracy), 2),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "fpr": round(float(fpr), 4),
        "fnr": round(float(fnr), 4),
        "total_records": int(len(dataframe)),
        "total_anomalies": int(y_pred.sum()),
        "true_anomalies": int(y_true.sum()),
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
    }


def save_metrics(dataset_id: int, model_name: str, metrics: dict) -> None:
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
            metrics["total_records"],
            metrics["total_anomalies"],
        ),
    )


def evaluate_active_dataset(model_names: Optional[Sequence[str]] = None) -> int:
    dataset_id = get_active_dataset_id()

    if model_names is None:
        model_names_to_evaluate = get_model_names_for_dataset(dataset_id)
    else:
        model_names_to_evaluate = list(model_names)

    if not model_names_to_evaluate:
        raise RuntimeError("No anomaly_results found. Train models before evaluation.")

    print("Model evaluation started.")
    print(f"Dataset ID: {dataset_id}")
    print(f"Models to evaluate: {', '.join(model_names_to_evaluate)}")

    for model_name in model_names_to_evaluate:
        evaluation_dataframe = load_evaluation_data(dataset_id, model_name)
        metrics = calculate_metrics(evaluation_dataframe)
        save_metrics(dataset_id, model_name, metrics)

        print("-" * 60)
        print(f"Model: {model_name}")
        print(f"Accuracy: {metrics['accuracy']}%")
        print(f"Precision: {metrics['precision']}")
        print(f"Recall: {metrics['recall']}")
        print(f"FPR: {metrics['fpr']}")
        print(f"FNR: {metrics['fnr']}")
        print(f"True anomalies in dataset: {metrics['true_anomalies']}")
        print(f"Predicted anomalies: {metrics['total_anomalies']}")
        print(
            "Confusion matrix: "
            f"TP={metrics['tp']}, TN={metrics['tn']}, FP={metrics['fp']}, FN={metrics['fn']}"
        )

    execute_query(
        """
        UPDATE datasets
        SET status = 'evaluated'
        WHERE id = %s;
        """,
        (dataset_id,),
    )

    print("-" * 60)
    print("Model evaluation completed successfully.")

    return dataset_id


def main():
    evaluate_active_dataset()


if __name__ == "__main__":
    main()