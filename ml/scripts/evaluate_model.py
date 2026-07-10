from typing import Optional, Sequence

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
)

from db import fetch_one, fetch_all, execute_query


TRAIN_RATIO = 0.70

SUPERVISED_MODEL_NAMES = {
    "Logistic Regression",
    "Decision Tree",
    "Random Forest",
    "Gradient Boosting",
    "KNN Classifier",
}


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


def keep_test_part(dataframe: pd.DataFrame) -> pd.DataFrame:
    # metrics are calculated only on the later test part
    split_index = int(len(dataframe) * TRAIN_RATIO)

    if split_index <= 0 or split_index >= len(dataframe):
        return dataframe

    return dataframe.iloc[split_index:].copy()


def load_labeled_evaluation_data(dataset_id: int, model_name: str) -> pd.DataFrame:
    rows = fetch_all(
        """
        SELECT
            ar.timestamp,
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
        return dataframe

    dataframe["timestamp"] = pd.to_datetime(dataframe["timestamp"])

    return keep_test_part(dataframe)


def load_unsupervised_summary(dataset_id: int, model_name: str) -> dict:
    row = fetch_one(
        """
        SELECT
            COUNT(*) AS total_records,
            COALESCE(SUM(CASE WHEN predicted_anomaly = TRUE THEN 1 ELSE 0 END), 0) AS total_anomalies,
            AVG(anomaly_score) AS score_mean,
            STDDEV_POP(anomaly_score) AS score_std,
            VAR_POP(anomaly_score) AS score_variance
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
            "score_mean": None,
            "score_std": None,
            "score_variance": None,
        }

    return {
        "total_records": int(row["total_records"] or 0),
        "total_anomalies": int(row["total_anomalies"] or 0),
        "score_mean": round(float(row["score_mean"]), 6) if row["score_mean"] is not None else None,
        "score_std": round(float(row["score_std"]), 6) if row["score_std"] is not None else None,
        "score_variance": round(float(row["score_variance"]), 6) if row["score_variance"] is not None else None,
    }


def calculate_labeled_metrics(dataframe: pd.DataFrame, evaluation_mode: str) -> dict:
    y_true = dataframe["original_label"].astype(bool)
    y_pred = dataframe["predicted_anomaly"].astype(bool)
    y_score = pd.to_numeric(dataframe["anomaly_score"], errors="coerce").fillna(0)

    accuracy = accuracy_score(y_true, y_pred) * 100
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    has_both_classes = y_true.nunique() == 2

    roc_auc = None
    pr_auc = None

    if has_both_classes:
        roc_auc = roc_auc_score(y_true, y_score)
        pr_auc = average_precision_score(y_true, y_score)

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        y_pred,
        labels=[False, True],
    ).ravel()

    fpr = fp / (fp + tn) if (fp + tn) else 0
    fnr = fn / (fn + tp) if (fn + tp) else 0

    return {
        "evaluation_mode": evaluation_mode,
        "accuracy": round(float(accuracy), 2),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(f1), 4),
        "roc_auc": round(float(roc_auc), 4) if roc_auc is not None else None,
        "pr_auc": round(float(pr_auc), 4) if pr_auc is not None else None,
        "fpr": round(float(fpr), 4),
        "fnr": round(float(fnr), 4),
        "total_records": int(len(dataframe)),
        "total_anomalies": int(y_pred.sum()),
        "true_anomalies": int(y_true.sum()),
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "score_mean": round(float(y_score.mean()), 6),
        "score_std": round(float(y_score.std()), 6),
        "score_variance": round(float(y_score.var()), 6),
        "training_time_seconds": None,
        "prediction_time_seconds": None,
    }


def calculate_unsupervised_metrics(dataset_id: int, model_name: str) -> dict:
    summary = load_unsupervised_summary(dataset_id, model_name)

    return {
        "evaluation_mode": "unsupervised",
        "accuracy": None,
        "precision": None,
        "recall": None,
        "f1_score": None,
        "roc_auc": None,
        "pr_auc": None,
        "fpr": None,
        "fnr": None,
        "total_records": summary["total_records"],
        "total_anomalies": summary["total_anomalies"],
        "true_anomalies": None,
        "tp": 0,
        "tn": 0,
        "fp": 0,
        "fn": 0,
        "score_mean": summary["score_mean"],
        "score_std": summary["score_std"],
        "score_variance": summary["score_variance"],
        "training_time_seconds": None,
        "prediction_time_seconds": None,
    }


def get_evaluation_mode(model_name: str) -> str:
    if model_name in SUPERVISED_MODEL_NAMES:
        return "supervised"

    return "labeled"


def attach_model_timing(metrics: dict, model_name: str, model_timings: Optional[dict]) -> dict:
    if not model_timings:
        return metrics

    timing = model_timings.get(model_name)

    if not timing:
        return metrics

    metrics["training_time_seconds"] = timing.get("training_time_seconds")
    metrics["prediction_time_seconds"] = timing.get("prediction_time_seconds")

    return metrics


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
            metrics.get("accuracy"),
            metrics.get("precision"),
            metrics.get("recall"),
            metrics.get("f1_score"),
            metrics.get("roc_auc"),
            metrics.get("pr_auc"),
            metrics.get("fpr"),
            metrics.get("fnr"),
            metrics.get("tp"),
            metrics.get("tn"),
            metrics.get("fp"),
            metrics.get("fn"),
            metrics.get("true_anomalies"),
            metrics.get("total_records"),
            metrics.get("total_anomalies"),
            metrics.get("score_mean"),
            metrics.get("score_std"),
            metrics.get("score_variance"),
            metrics.get("training_time_seconds"),
            metrics.get("prediction_time_seconds"),
            metrics.get("evaluation_mode"),
        ),
    )


def evaluate_active_dataset(
        model_names: Optional[Sequence[str]] = None,
        model_timings: Optional[dict] = None,
) -> int:
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

        if not labeled_dataframe.empty:
            metrics = calculate_labeled_metrics(
                dataframe=labeled_dataframe,
                evaluation_mode=get_evaluation_mode(model_name),
            )
        else:
            metrics = calculate_unsupervised_metrics(dataset_id, model_name)

        metrics = attach_model_timing(metrics, model_name, model_timings)

        save_metrics(dataset_id, model_name, metrics)

        print("-" * 60)
        print(f"Model: {model_name}")
        print(f"Evaluation mode: {metrics['evaluation_mode']}")

        if metrics["evaluation_mode"] in ("supervised", "labeled"):
            print(f"Accuracy: {metrics['accuracy']}%")
            print(f"Precision: {metrics['precision']}")
            print(f"Recall: {metrics['recall']}")
            print(f"F1-score: {metrics['f1_score']}")
            print(f"ROC-AUC: {metrics['roc_auc']}")
            print(f"PR-AUC: {metrics['pr_auc']}")
            print(f"FPR: {metrics['fpr']}")
            print(f"FNR: {metrics['fnr']}")
            print(f"True anomalies in test set: {metrics['true_anomalies']}")
            print(
                "Confusion matrix on TEST: "
                f"TP={metrics['tp']}, TN={metrics['tn']}, FP={metrics['fp']}, FN={metrics['fn']}"
            )
        else:
            print("No original anomaly labels found.")
            print("Supervised metrics were saved as NULL.")
            print("This is expected for real unlabeled radiation data.")

        print(f"Total records used for metrics: {metrics['total_records']}")
        print(f"Predicted anomalies used for metrics: {metrics['total_anomalies']}")
        print(f"Training time: {metrics['training_time_seconds']}")
        print(f"Prediction time: {metrics['prediction_time_seconds']}")

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
