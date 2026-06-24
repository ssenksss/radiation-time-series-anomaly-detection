from typing import Optional

from app.database.connection import fetch_one


AVAILABLE_MODELS = [
    {
        "id": "isolation_forest",
        "name": "Isolation Forest",
        "status": "implemented",
    },
    {
        "id": "lof",
        "name": "Local Outlier Factor",
        "status": "implemented",
    },
    {
        "id": "rnn",
        "name": "Recurrent Neural Network",
        "status": "pending",
    },
]


MODEL_ID_TO_NAME = {
    "isolation_forest": "Isolation Forest",
    "lof": "Local Outlier Factor",
    "rnn": "Recurrent Neural Network",
}

VALID_MODEL_IDS = {"isolation_forest", "lof", "rnn"}


def normalize_model_id(model_id: Optional[str], fallback: str = "isolation_forest") -> str:
    if not model_id:
        return fallback

    normalized = model_id.strip().lower().replace("-", "_").replace(" ", "_")

    aliases = {
        "isolation_forest": "isolation_forest",
        "isolationforest": "isolation_forest",
        "isolation": "isolation_forest",
        "iforest": "isolation_forest",

        "local_outlier_factor": "lof",
        "localoutlierfactor": "lof",
        "lof": "lof",

        "recurrent_neural_network": "rnn",
        "rnn": "rnn",
    }

    resolved = aliases.get(normalized, normalized)

    if resolved in VALID_MODEL_IDS:
        return resolved

    return fallback


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


def get_active_model_id() -> str:
    row = fetch_one(
        """
        SELECT value
        FROM app_settings
        WHERE key = 'active_model';
        """
    )

    if not row:
        return "isolation_forest"

    return normalize_model_id(str(row["value"]), "isolation_forest")


def get_latest_metrics_for_model(dataset_id: int, model_name: str) -> dict:
    row = fetch_one(
        """
        SELECT
            model_name,
            accuracy,
            precision_score,
            recall_score,
            fpr,
            fnr,
            total_records,
            total_anomalies,
            created_at
        FROM model_metrics
        WHERE dataset_id = %s
          AND model_name = %s
        ORDER BY created_at DESC
        LIMIT 1;
        """,
        (dataset_id, model_name),
    )

    if not row:
        return {
            "model_name": model_name,
            "accuracy": None,
            "precision_score": None,
            "recall_score": None,
            "fpr": None,
            "fnr": None,
            "total_records": 0,
            "total_anomalies": 0,
            "created_at": None,
        }

    return row


def get_confusion_matrix(dataset_id: int, model_name: str) -> dict:
    row = fetch_one(
        """
        SELECT
            SUM(CASE WHEN cm.original_label = TRUE AND ar.predicted_anomaly = TRUE THEN 1 ELSE 0 END) AS tp,
            SUM(CASE WHEN cm.original_label = FALSE AND ar.predicted_anomaly = FALSE THEN 1 ELSE 0 END) AS tn,
            SUM(CASE WHEN cm.original_label = FALSE AND ar.predicted_anomaly = TRUE THEN 1 ELSE 0 END) AS fp,
            SUM(CASE WHEN cm.original_label = TRUE AND ar.predicted_anomaly = FALSE THEN 1 ELSE 0 END) AS fn
        FROM anomaly_results ar
        JOIN feature_measurements fm
            ON ar.feature_measurement_id = fm.id
        JOIN clean_measurements cm
            ON fm.clean_measurement_id = cm.id
        WHERE ar.dataset_id = %s
          AND ar.model_name = %s
          AND cm.original_label IS NOT NULL;
        """,
        (dataset_id, model_name),
    )

    if not row:
        return {"tp": 0, "tn": 0, "fp": 0, "fn": 0}

    return {
        "tp": int(row["tp"] or 0),
        "tn": int(row["tn"] or 0),
        "fp": int(row["fp"] or 0),
        "fn": int(row["fn"] or 0),
    }


def normalize_selection(model_a: Optional[str], model_b: Optional[str]) -> tuple[str, str]:
    active_model = get_active_model_id()

    selected_a = normalize_model_id(model_a, active_model)
    selected_b = normalize_model_id(model_b, "lof" if selected_a != "lof" else "isolation_forest")

    if selected_a == selected_b:
        selected_b = "lof" if selected_a != "lof" else "isolation_forest"

    return selected_a, selected_b


def build_model_item(model_id: str, metrics: dict, active_model_id: str) -> dict:
    model_name = MODEL_ID_TO_NAME.get(model_id, "Unknown Model")
    is_pending = model_id == "rnn" or metrics["accuracy"] is None

    if is_pending:
        return {
            "id": model_id,
            "model": model_name,
            "score": None,
            "accuracy": None,
            "precision": None,
            "recall": None,
            "fpr": None,
            "fnr": None,
            "totalRecords": int(metrics.get("total_records") or 0),
            "totalAnomalies": int(metrics.get("total_anomalies") or 0),
            "active": model_id == active_model_id,
            "status": "Pending ML implementation" if model_id == "rnn" else "No metrics available",
        }

    accuracy = round(float(metrics["accuracy"] or 0), 2)
    precision = round(float(metrics["precision_score"] or 0), 4)
    recall = round(float(metrics["recall_score"] or 0), 4)
    fpr = round(float(metrics["fpr"] or 0), 4)
    fnr = round(float(metrics["fnr"] or 0), 4)

    return {
        "id": model_id,
        "model": model_name,
        "score": accuracy,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "fpr": fpr,
        "fnr": fnr,
        "totalRecords": int(metrics["total_records"] or 0),
        "totalAnomalies": int(metrics["total_anomalies"] or 0),
        "active": model_id == active_model_id,
        "status": "Active" if model_id == active_model_id else "Implemented",
    }


def get_model_info_from_database(
        model_a: Optional[str] = None,
        model_b: Optional[str] = None,
) -> dict:
    dataset_id = get_active_dataset_id()
    active_model_id = get_active_model_id()

    selected_model_a, selected_model_b = normalize_selection(model_a, model_b)

    isolation_metrics = get_latest_metrics_for_model(dataset_id, "Isolation Forest")
    lof_metrics = get_latest_metrics_for_model(dataset_id, "Local Outlier Factor")

    empty_rnn_metrics = {
        "model_name": "Recurrent Neural Network",
        "accuracy": None,
        "precision_score": None,
        "recall_score": None,
        "fpr": None,
        "fnr": None,
        "total_records": 0,
        "total_anomalies": 0,
        "created_at": None,
    }

    metrics_by_id = {
        "isolation_forest": isolation_metrics,
        "lof": lof_metrics,
        "rnn": empty_rnn_metrics,
    }

    active_metrics = metrics_by_id.get(active_model_id, isolation_metrics)
    active_model_name = MODEL_ID_TO_NAME.get(active_model_id, "Isolation Forest")
    confusion_matrix = get_confusion_matrix(dataset_id, active_model_name)

    accuracy = round(float(active_metrics["accuracy"] or 0), 2)
    precision = round(float(active_metrics["precision_score"] or 0), 4)
    recall = round(float(active_metrics["recall_score"] or 0), 4)
    fpr = round(float(active_metrics["fpr"] or 0), 4)
    fnr = round(float(active_metrics["fnr"] or 0), 4)

    response = {
        "currentModel": active_model_name,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "fpr": fpr,
        "fnr": fnr,
        "source": "Model metrics loaded from PostgreSQL model_metrics table.",
        "availableModels": AVAILABLE_MODELS,
        "selectedModels": {
            "modelA": selected_model_a,
            "modelB": selected_model_b,
        },
        "confusionMatrix": confusion_matrix,
        "totalRecords": int(active_metrics["total_records"] or 0),
        "totalAnomalies": int(active_metrics["total_anomalies"] or 0),
        "comparison": [
            build_model_item(selected_model_a, metrics_by_id[selected_model_a], active_model_id),
            build_model_item(selected_model_b, metrics_by_id[selected_model_b], active_model_id),
        ],
    }

    if active_metrics["created_at"]:
        response["lastTrainedAt"] = active_metrics["created_at"].strftime("%Y-%m-%d %H:%M:%S")

    return response