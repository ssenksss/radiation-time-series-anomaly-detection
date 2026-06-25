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


def get_model_names_for_dataset(dataset_id: int) -> list[str]:
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


def load_labeled_evaluation_data(dataset_id: int, model_name: str) -> pd.DataFrame:
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

    return pd.DataFrame(rows)


def load_unsupervised_summary(dataset_id: int, model_name: str) -> dict:
    row = fetch_one(
        """
        SELECT
            COUNT(*) AS total_records,
            COALESCE(SUM(CASE WHEN predicted_anomaly = TRUE THEN 1 ELSE 0 END), 0) AS total_anomalies
        FROM anomaly_results
        WHERE dataset_id = %s
          AND model_name = %s;
        """,
        (dataset_id, model_name),
    )

    if not row:
        return {
            "total_records": 0,
            "total_anomalies": 0,
        }

    return {
        "total_records": int(row["total_records"] or 0),
        "total_anomalies": int(row["total_anomalies"] or 0),
    }


def calculate_supervised_metrics(dataframe: pd.DataFrame) -> dict:
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
        "evaluation_mode": "supervised",
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


def calculate_unsupervised_metrics(dataset_id: int, model_name: str) -> dict:
    summary = load_unsupervised_summary(dataset_id, model_name)

    return {
        "evaluation_mode": "unsupervised",
        "accuracy": None,
        "precision": None,
        "recall": None,
        "fpr": None,
        "fnr": None,
        "total_records": summary["total_records"],
        "total_anomalies": summary["total_anomalies"],
        "true_anomalies": None,
        "tp": 0,
        "tn": 0,
        "fp": 0,
        "fn": 0,
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
        labeled_dataframe = load_labeled_evaluation_data(dataset_id, model_name)

        has_usable_labels = False

        if not labeled_dataframe.empty:
            labels = labeled_dataframe["original_label"].astype(bool)
            has_usable_labels = bool(labels.any())

        if has_usable_labels:
            metrics = calculate_supervised_metrics(labeled_dataframe)
        else:
            metrics = calculate_unsupervised_metrics(dataset_id, model_name)

        save_metrics(dataset_id, model_name, metrics)

        print("-" * 60)
        print(f"Model: {model_name}")
        print(f"Evaluation mode: {metrics['evaluation_mode']}")

        if metrics["evaluation_mode"] == "supervised":
            print(f"Accuracy: {metrics['accuracy']}%")
            print(f"Precision: {metrics['precision']}")
            print(f"Recall: {metrics['recall']}")
            print(f"FPR: {metrics['fpr']}")
            print(f"FNR: {metrics['fnr']}")
            print(f"True anomalies in dataset: {metrics['true_anomalies']}")
            print(
                "Confusion matrix: "
                f"TP={metrics['tp']}, TN={metrics['tn']}, FP={metrics['fp']}, FN={metrics['fn']}"
            )
        else:
            print("No original anomaly labels found.")
            print("Supervised metrics were saved as NULL.")
            print("This is expected for real unlabeled radiation data.")

        print(f"Total records: {metrics['total_records']}")
        print(f"Predicted anomalies: {metrics['total_anomalies']}")

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