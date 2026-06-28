from typing import Dict, List, Optional, Tuple

from app.database.connection import fetch_one


UNSUPERVISED_MODELS = [
    {
        "id": "isolation_forest",
        "name": "Isolation Forest",
        "category": "unsupervised",
        "requiresLabels": False,
        "status": "implemented",
    },
    {
        "id": "lof",
        "name": "Local Outlier Factor",
        "category": "unsupervised",
        "requiresLabels": False,
        "status": "implemented",
    },
    {
        "id": "one_class_svm",
        "name": "One-Class SVM",
        "category": "unsupervised",
        "requiresLabels": False,
        "status": "implemented",
    },
    {
        "id": "elliptic_envelope",
        "name": "Elliptic Envelope",
        "category": "unsupervised",
        "requiresLabels": False,
        "status": "implemented",
    },
    {
        "id": "dbscan",
        "name": "DBSCAN",
        "category": "unsupervised",
        "requiresLabels": False,
        "status": "implemented",
    },
    {
        "id": "kmeans_distance",
        "name": "K-Means Distance",
        "category": "unsupervised",
        "requiresLabels": False,
        "status": "implemented",
    },
    {
        "id": "gaussian_mixture",
        "name": "Gaussian Mixture Model",
        "category": "unsupervised",
        "requiresLabels": False,
        "status": "implemented",
    },
    {
        "id": "pca_reconstruction",
        "name": "PCA Reconstruction Error",
        "category": "unsupervised",
        "requiresLabels": False,
        "status": "implemented",
    },
    {
        "id": "hbos",
        "name": "HBOS",
        "category": "unsupervised",
        "requiresLabels": False,
        "status": "implemented",
    },
    {
        "id": "ecod",
        "name": "ECOD",
        "category": "unsupervised",
        "requiresLabels": False,
        "status": "implemented",
    },
]

SUPERVISED_MODELS = [
    {
        "id": "logistic_regression",
        "name": "Logistic Regression",
        "category": "supervised",
        "requiresLabels": True,
        "status": "implemented",
    },
    {
        "id": "decision_tree",
        "name": "Decision Tree",
        "category": "supervised",
        "requiresLabels": True,
        "status": "implemented",
    },
    {
        "id": "random_forest",
        "name": "Random Forest",
        "category": "supervised",
        "requiresLabels": True,
        "status": "implemented",
    },
    {
        "id": "gradient_boosting",
        "name": "Gradient Boosting",
        "category": "supervised",
        "requiresLabels": True,
        "status": "implemented",
    },
    {
        "id": "knn_classifier",
        "name": "KNN Classifier",
        "category": "supervised",
        "requiresLabels": True,
        "status": "implemented",
    },
]

FUTURE_MODELS = [
    {
        "id": "rnn",
        "name": "Recurrent Neural Network",
        "category": "future",
        "requiresLabels": False,
        "status": "pending",
    },
]

AVAILABLE_MODELS = UNSUPERVISED_MODELS + SUPERVISED_MODELS + FUTURE_MODELS

MODEL_ID_TO_NAME = {model["id"]: model["name"] for model in AVAILABLE_MODELS}
MODEL_ID_TO_CATEGORY = {model["id"]: model["category"] for model in AVAILABLE_MODELS}
MODEL_ID_REQUIRES_LABELS = {model["id"]: model["requiresLabels"] for model in AVAILABLE_MODELS}
VALID_MODEL_IDS = set(MODEL_ID_TO_NAME.keys())


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

        "one_class_svm": "one_class_svm",
        "oneclasssvm": "one_class_svm",
        "ocsvm": "one_class_svm",

        "elliptic_envelope": "elliptic_envelope",
        "ellipticenvelope": "elliptic_envelope",

        "dbscan": "dbscan",

        "kmeans_distance": "kmeans_distance",
        "k_means_distance": "kmeans_distance",
        "kmeans": "kmeans_distance",

        "gaussian_mixture": "gaussian_mixture",
        "gaussian_mixture_model": "gaussian_mixture",
        "gmm": "gaussian_mixture",

        "pca_reconstruction": "pca_reconstruction",
        "pca_reconstruction_error": "pca_reconstruction",
        "pca": "pca_reconstruction",

        "hbos": "hbos",
        "ecod": "ecod",

        "logistic_regression": "logistic_regression",
        "logreg": "logistic_regression",

        "decision_tree": "decision_tree",
        "decisiontree": "decision_tree",

        "random_forest": "random_forest",
        "randomforest": "random_forest",

        "gradient_boosting": "gradient_boosting",
        "gradientboosting": "gradient_boosting",

        "knn_classifier": "knn_classifier",
        "knn": "knn_classifier",

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


def dataset_has_labels(dataset_id: int) -> bool:
    row = fetch_one(
        """
        SELECT COUNT(*) AS labeled_rows
        FROM clean_measurements
        WHERE dataset_id = %s
          AND original_label IS NOT NULL;
        """,
        (dataset_id,),
    )

    if not row:
        return False

    return int(row["labeled_rows"] or 0) > 0


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


def build_available_models(has_labels: bool) -> List[dict]:
    models = []

    for model in AVAILABLE_MODELS:
        requires_labels = bool(model["requiresLabels"])
        enabled = model["status"] == "implemented" and (has_labels or not requires_labels)

        item = dict(model)
        item["enabled"] = enabled
        item["disabledReason"] = None

        if model["status"] != "implemented":
            item["disabledReason"] = "Pending implementation"

        if requires_labels and not has_labels:
            item["disabledReason"] = "Requires labeled dataset with is_anomaly column"

        models.append(item)

    return models


def normalize_selection(
        model_a: Optional[str],
        model_b: Optional[str],
        has_labels: bool,
) -> Tuple[str, str]:
    active_model = get_active_model_id()

    selected_a = normalize_model_id(model_a, active_model)
    selected_b = normalize_model_id(model_b, "hbos" if selected_a != "hbos" else "kmeans_distance")

    def is_allowed(model_id: str) -> bool:
        if model_id == "rnn":
            return False

        if MODEL_ID_REQUIRES_LABELS.get(model_id, False) and not has_labels:
            return False

        return model_id in VALID_MODEL_IDS

    if not is_allowed(selected_a):
        selected_a = "hbos"

    if not is_allowed(selected_b) or selected_b == selected_a:
        selected_b = "kmeans_distance" if selected_a != "kmeans_distance" else "hbos"

    return selected_a, selected_b


def get_evaluation_mode(metrics: dict, model_id: str, has_labels: bool) -> str:
    if model_id == "rnn":
        return "pending"

    total_records = int(metrics.get("total_records") or 0)

    if total_records <= 0:
        return "pending"

    if MODEL_ID_TO_CATEGORY.get(model_id) == "supervised":
        return "supervised"

    if has_labels and metrics.get("accuracy") is not None:
        return "supervised"

    return "unsupervised"


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
        has_labels: bool,
) -> dict:
    model_name = MODEL_ID_TO_NAME.get(model_id, "Unknown Model")
    category = MODEL_ID_TO_CATEGORY.get(model_id, "unknown")
    requires_labels = MODEL_ID_REQUIRES_LABELS.get(model_id, False)
    enabled = not requires_labels or has_labels

    evaluation_mode = get_evaluation_mode(metrics, model_id, has_labels)

    total_records = int(metrics.get("total_records") or 0)
    total_anomalies = int(metrics.get("total_anomalies") or 0)
    model_score = calculate_model_score(dataset_id, model_name, metrics)
    anomaly_rate = calculate_anomaly_rate(metrics)

    base = {
        "id": model_id,
        "model": model_name,
        "category": category,
        "requiresLabels": requires_labels,
        "enabled": enabled,
        "disabledReason": None if enabled else "Requires labeled dataset with is_anomaly column",
        "active": model_id == active_model_id,
        "evaluationMode": evaluation_mode,
        "totalRecords": total_records,
        "totalAnomalies": total_anomalies,
        "anomalyRate": anomaly_rate,
    }

    if evaluation_mode == "pending":
        return {
            **base,
            "score": None,
            "modelScore": None,
            "accuracy": None,
            "precision": None,
            "recall": None,
            "fpr": None,
            "fnr": None,
            "status": "Pending ML implementation" if model_id == "rnn" else "No metrics available",
        }

    if evaluation_mode == "unsupervised":
        return {
            **base,
            "score": model_score,
            "modelScore": model_score,
            "accuracy": None,
            "precision": None,
            "recall": None,
            "fpr": None,
            "fnr": None,
            "status": "Active" if model_id == active_model_id else "Implemented",
        }

    accuracy = round(float(metrics["accuracy"] or 0), 2)
    precision = round(float(metrics["precision_score"] or 0), 4)
    recall = round(float(metrics["recall_score"] or 0), 4)
    fpr = round(float(metrics["fpr"] or 0), 4)
    fnr = round(float(metrics["fnr"] or 0), 4)

    return {
        **base,
        "score": accuracy,
        "modelScore": model_score,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "fpr": fpr,
        "fnr": fnr,
        "status": "Active" if model_id == active_model_id else "Implemented",
    }


def get_metrics_by_id(dataset_id: int) -> Dict[str, dict]:
    metrics_by_id = {}

    for model_id, model_name in MODEL_ID_TO_NAME.items():
        metrics_by_id[model_id] = get_latest_metrics_for_model(dataset_id, model_name)

    return metrics_by_id


def get_model_info_from_database(
        model_a: Optional[str] = None,
        model_b: Optional[str] = None,
) -> dict:
    dataset_id = get_active_dataset_id()
    has_labels = dataset_has_labels(dataset_id)

    active_model_id = get_active_model_id()

    if MODEL_ID_REQUIRES_LABELS.get(active_model_id, False) and not has_labels:
        active_model_id = "hbos"

    selected_model_a, selected_model_b = normalize_selection(model_a, model_b, has_labels)

    metrics_by_id = get_metrics_by_id(dataset_id)

    active_metrics = metrics_by_id.get(active_model_id, metrics_by_id["hbos"])
    active_model_name = MODEL_ID_TO_NAME.get(active_model_id, "HBOS")
    active_evaluation_mode = get_evaluation_mode(active_metrics, active_model_id, has_labels)
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

    comparison = [
        build_model_item(
            selected_model_a,
            metrics_by_id[selected_model_a],
            active_model_id,
            dataset_id,
            has_labels,
        ),
        build_model_item(
            selected_model_b,
            metrics_by_id[selected_model_b],
            active_model_id,
            dataset_id,
            has_labels,
        ),
    ]

    response = {
        "currentModel": active_model_name,
        "activeModelId": active_model_id,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "fpr": fpr,
        "fnr": fnr,
        "modelScore": active_model_score,
        "evaluationMode": active_evaluation_mode,
        "datasetHasLabels": has_labels,
        "hasLabels": has_labels,
        "totalRecords": int(active_metrics["total_records"] or 0),
        "totalAnomalies": int(active_metrics["total_anomalies"] or 0),
        "anomalyRate": active_anomaly_rate,
        "source": "Model metrics loaded from PostgreSQL model_metrics table.",
        "availableModels": build_available_models(has_labels),
        "selectedModels": {
            "modelA": selected_model_a,
            "modelB": selected_model_b,
        },
        "confusionMatrix": confusion_matrix,
        "comparison": comparison,
        "groups": {
            "unsupervised": [model["id"] for model in UNSUPERVISED_MODELS],
            "supervised": [model["id"] for model in SUPERVISED_MODELS],
            "future": [model["id"] for model in FUTURE_MODELS],
        },
    }

    if active_metrics["created_at"]:
        response["lastTrainedAt"] = active_metrics["created_at"].strftime("%Y-%m-%d %H:%M:%S")

    return response