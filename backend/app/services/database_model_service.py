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


def get_model_score_stats(dataset_id: int, model_name: str) -> dict:
    row = fetch_one(
        """
        SELECT
            COUNT(*) AS total_records,
            SUM(CASE WHEN predicted_anomaly = TRUE THEN 1 ELSE 0 END) AS total_anomalies,
            AVG(anomaly_score) AS avg_score,
            AVG(CASE WHEN predicted_anomaly = TRUE THEN anomaly_score ELSE NULL END) AS avg_anomaly_score,
            AVG(CASE WHEN predicted_anomaly = FALSE THEN anomaly_score ELSE NULL END) AS avg_normal_score,
            MIN(anomaly_score) AS min_score,
            MAX(anomaly_score) AS max_score
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
            "avg_score": None,
            "avg_anomaly_score": None,
            "avg_normal_score": None,
            "min_score": None,
            "max_score": None,
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


def get_evaluation_mode(metrics: dict, model_id: str) -> str:
    if model_id == "rnn":
        return "pending"

    total_records = int(metrics.get("total_records") or 0)

    if total_records <= 0:
        return "pending"

    if metrics.get("accuracy") is None:
        return "unsupervised"

    return "supervised"


def calculate_model_score(dataset_id: int, model_name: str, metrics: dict) -> Optional[float]:
    total_records = int(metrics.get("total_records") or 0)
    total_anomalies = int(metrics.get("total_anomalies") or 0)

    if total_records <= 0:
        return None

    if total_anomalies <= 0:
        return 100.0

    score_stats = get_model_score_stats(dataset_id, model_name)

    anomaly_rate = total_anomalies / total_records

    avg_anomaly_score = score_stats.get("avg_anomaly_score")
    avg_normal_score = score_stats.get("avg_normal_score")
    min_score = score_stats.get("min_score")
    max_score = score_stats.get("max_score")

    if (
            avg_anomaly_score is None
            or avg_normal_score is None
            or min_score is None
            or max_score is None
    ):
        fallback_score = (1 - anomaly_rate) * 100
        return round(max(0, min(100, fallback_score)), 2)

    avg_anomaly_score = float(avg_anomaly_score)
    avg_normal_score = float(avg_normal_score)
    min_score = float(min_score)
    max_score = float(max_score)

    score_range = max_score - min_score

    if score_range <= 0:
        fallback_score = (1 - anomaly_rate) * 100
        return round(max(0, min(100, fallback_score)), 2)

    separation = abs(avg_anomaly_score - avg_normal_score) / score_range
    separation = max(0, min(1, separation))

    normal_rate_component = (1 - anomaly_rate) * 70
    separation_component = separation * 30

    model_score = normal_rate_component + separation_component

    return round(max(0, min(100, model_score)), 2)


def calculate_anomaly_rate(metrics: dict) -> Optional[float]:
    total_records = int(metrics.get("total_records") or 0)
    total_anomalies = int(metrics.get("total_anomalies") or 0)

    if total_records <= 0:
        return None

    return round((total_anomalies / total_records) * 100, 3)


def build_model_item(
        model_id: str,
        metrics: dict,
        active_model_id: str,
        dataset_id: int,
) -> dict:
    model_name = MODEL_ID_TO_NAME.get(model_id, "Unknown Model")
    evaluation_mode = get_evaluation_mode(metrics, model_id)

    total_records = int(metrics.get("total_records") or 0)
    total_anomalies = int(metrics.get("total_anomalies") or 0)
    model_score = calculate_model_score(dataset_id, model_name, metrics)
    anomaly_rate = calculate_anomaly_rate(metrics)

    if evaluation_mode == "pending":
        return {
            "id": model_id,
            "model": model_name,
            "score": None,
            "modelScore": None,
            "accuracy": None,
            "precision": None,
            "recall": None,
            "fpr": None,
            "fnr": None,
            "evaluationMode": "pending",
            "totalRecords": total_records,
            "totalAnomalies": total_anomalies,
            "anomalyRate": anomaly_rate,
            "active": model_id == active_model_id,
            "status": "Pending ML implementation" if model_id == "rnn" else "No metrics available",
        }

    if evaluation_mode == "unsupervised":
        return {
            "id": model_id,
            "model": model_name,
            "score": model_score,
            "modelScore": model_score,
            "accuracy": None,
            "precision": None,
            "recall": None,
            "fpr": None,
            "fnr": None,
            "evaluationMode": "unsupervised",
            "totalRecords": total_records,
            "totalAnomalies": total_anomalies,
            "anomalyRate": anomaly_rate,
            "active": model_id == active_model_id,
            "status": "Active" if model_id == active_model_id else "Implemented",
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
        "modelScore": model_score,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "fpr": fpr,
        "fnr": fnr,
        "evaluationMode": "supervised",
        "totalRecords": total_records,
        "totalAnomalies": total_anomalies,
        "anomalyRate": anomaly_rate,
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
    active_evaluation_mode = get_evaluation_mode(active_metrics, active_model_id)
    confusion_matrix = get_confusion_matrix(dataset_id, active_model_name)

    active_model_score = calculate_model_score(dataset_id, active_model_name, active_metrics)
    active_anomaly_rate = calculate_anomaly_rate(active_metrics)

    accuracy = None
    precision = None
    recall = None
    fpr = None
    fnr = None

    if active_evaluation_mode == "supervised":
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
        "modelScore": active_model_score,
        "evaluationMode": active_evaluation_mode,
        "totalRecords": int(active_metrics["total_records"] or 0),
        "totalAnomalies": int(active_metrics["total_anomalies"] or 0),
        "anomalyRate": active_anomaly_rate,
        "source": "Model metrics loaded from PostgreSQL model_metrics table.",
        "availableModels": AVAILABLE_MODELS,
        "selectedModels": {
            "modelA": selected_model_a,
            "modelB": selected_model_b,
        },
        "confusionMatrix": confusion_matrix,
        "comparison": [
            build_model_item(
                selected_model_a,
                metrics_by_id[selected_model_a],
                active_model_id,
                dataset_id,
            ),
            build_model_item(
                selected_model_b,
                metrics_by_id[selected_model_b],
                active_model_id,
                dataset_id,
            ),
        ],
    }

    if active_metrics["created_at"]:
        response["lastTrainedAt"] = active_metrics["created_at"].strftime("%Y-%m-%d %H:%M:%S")

    return response