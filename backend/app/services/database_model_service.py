from typing import Dict, List, Optional, Tuple

from sklearn.metrics import precision_recall_curve, roc_curve

from app.database.connection import fetch_one, fetch_all


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
            evaluation_mode,
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
            "f1_score": None,
            "roc_auc": None,
            "pr_auc": None,
            "fpr": None,
            "fnr": None,
            "tp": 0,
            "tn": 0,
            "fp": 0,
            "fn": 0,
            "true_anomalies": None,
            "total_records": 0,
            "total_anomalies": 0,
            "score_mean": None,
            "score_std": None,
            "score_variance": None,
            "training_time_seconds": None,
            "prediction_time_seconds": None,
            "evaluation_mode": None,
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
            tp,
            tn,
            fp,
            fn
        FROM model_metrics
        WHERE dataset_id = %s
          AND model_name = %s
        ORDER BY created_at DESC
        LIMIT 1;
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
        return "labeled"

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


MAX_CURVE_POINTS = 140
TRAIN_RATIO = 0.70


def downsample_curve_points(points: List[dict], max_points: int = MAX_CURVE_POINTS) -> List[dict]:
    if len(points) <= max_points:
        return points

    if max_points <= 2:
        return points[:max_points]

    last_index = len(points) - 1
    selected_indexes = {
        round(index * last_index / (max_points - 1))
        for index in range(max_points)
    }

    return [points[index] for index in sorted(selected_indexes)]


def load_labeled_curve_rows(dataset_id: int, model_name: str) -> List[dict]:
    rows = fetch_all(
        """
        SELECT
            ar.anomaly_score,
            cm.original_label,
            ar.timestamp
        FROM anomaly_results ar
        JOIN feature_measurements fm
            ON ar.feature_measurement_id = fm.id
        JOIN clean_measurements cm
            ON fm.clean_measurement_id = cm.id
        WHERE ar.dataset_id = %s
          AND ar.model_name = %s
          AND cm.original_label IS NOT NULL
          AND ar.anomaly_score IS NOT NULL
        ORDER BY ar.timestamp;
        """,
        (dataset_id, model_name),
    )

    return list(rows)


def get_curve_evaluation_rows(model_id: str, rows: List[dict]) -> Tuple[List[dict], str]:
    split_index = int(len(rows) * TRAIN_RATIO)

    if split_index <= 0 or split_index >= len(rows):
        return rows, "full labeled dataset"

    return rows[split_index:], "chronological test split"


def build_empty_curve_item(model_id: str, message: str) -> dict:
    return {
        "id": model_id,
        "model": MODEL_ID_TO_NAME.get(model_id, model_id),
        "category": MODEL_ID_TO_CATEGORY.get(model_id),
        "available": False,
        "message": message,
        "evaluationScope": None,
        "rocAuc": None,
        "prAuc": None,
        "rocCurve": [],
        "prCurve": [],
    }


def build_model_curve_item(dataset_id: int, model_id: str, metrics: dict) -> dict:
    if model_id == "rnn":
        return build_empty_curve_item(model_id, "RNN is planned for a future implementation phase.")

    model_name = MODEL_ID_TO_NAME.get(model_id)

    if not model_name:
        return build_empty_curve_item(model_id, "Unknown model.")

    rows = load_labeled_curve_rows(dataset_id, model_name)

    if not rows:
        return build_empty_curve_item(
            model_id,
            "ROC and Precision-Recall curves require original labels and anomaly scores.",
        )

    evaluation_rows, evaluation_scope = get_curve_evaluation_rows(model_id, rows)

    if len(evaluation_rows) < 2:
        return build_empty_curve_item(
            model_id,
            "Not enough labeled rows to calculate evaluation curves.",
        )

    y_true = [1 if row["original_label"] else 0 for row in evaluation_rows]
    y_score = [float(row["anomaly_score"] or 0) for row in evaluation_rows]

    if len(set(y_true)) < 2:
        return build_empty_curve_item(
            model_id,
            "Evaluation curves require both normal and anomaly examples.",
        )

    fpr_values, tpr_values, _ = roc_curve(y_true, y_score)
    precision_values, recall_values, _ = precision_recall_curve(y_true, y_score)

    roc_points = [
        {
            "x": round(float(fpr), 6),
            "y": round(float(tpr), 6),
        }
        for fpr, tpr in zip(fpr_values, tpr_values)
    ]

    pr_points = [
        {
            "x": round(float(recall), 6),
            "y": round(float(precision), 6),
        }
        for precision, recall in zip(precision_values, recall_values)
    ]
    pr_points = sorted(pr_points, key=lambda point: point["x"])

    return {
        "id": model_id,
        "model": model_name,
        "category": MODEL_ID_TO_CATEGORY.get(model_id),
        "available": True,
        "message": None,
        "evaluationScope": evaluation_scope,
        "rocAuc": round(float(metrics["roc_auc"]), 4) if metrics.get("roc_auc") is not None else None,
        "prAuc": round(float(metrics["pr_auc"]), 4) if metrics.get("pr_auc") is not None else None,
        "rocCurve": downsample_curve_points(roc_points),
        "prCurve": downsample_curve_points(pr_points),
    }


def get_model_curves_from_database(
        model_a: Optional[str] = None,
        model_b: Optional[str] = None,
) -> dict:
    dataset_id = get_active_dataset_id()
    has_labels = dataset_has_labels(dataset_id)

    selected_model_a, selected_model_b = normalize_selection(model_a, model_b, has_labels)

    if not has_labels:
        return {
            "datasetId": dataset_id,
            "datasetHasLabels": False,
            "selectedModels": {
                "modelA": selected_model_a,
                "modelB": selected_model_b,
            },
            "available": False,
            "message": "ROC and Precision-Recall curves are available only for labeled datasets.",
            "curves": [],
        }

    metrics_by_id = get_metrics_by_id(dataset_id)

    curves = [
        build_model_curve_item(dataset_id, selected_model_a, metrics_by_id[selected_model_a]),
        build_model_curve_item(dataset_id, selected_model_b, metrics_by_id[selected_model_b]),
    ]

    return {
        "datasetId": dataset_id,
        "datasetHasLabels": True,
        "selectedModels": {
            "modelA": selected_model_a,
            "modelB": selected_model_b,
        },
        "available": any(curve["available"] for curve in curves),
        "message": None if any(curve["available"] for curve in curves) else "No curve data available for selected models.",
        "curves": curves,
    }


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
                "f1Score": metrics.get("f1_score"),
        "rocAuc": metrics.get("roc_auc"),
        "prAuc": metrics.get("pr_auc"),
        "tp": int(metrics.get("tp") or 0),
        "tn": int(metrics.get("tn") or 0),
        "fp": int(metrics.get("fp") or 0),
        "fn": int(metrics.get("fn") or 0),
        "trueAnomalies": metrics.get("true_anomalies"),
        "scoreMean": metrics.get("score_mean"),
        "scoreStd": metrics.get("score_std"),
        "scoreVariance": metrics.get("score_variance"),
        "trainingTimeSeconds": metrics.get("training_time_seconds"),
        "predictionTimeSeconds": metrics.get("prediction_time_seconds"),
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
    f1_score_value = None
    roc_auc = None
    pr_auc = None
    fpr = None
    fnr = None

    if active_evaluation_mode in ("supervised", "labeled"):
        accuracy = round(float(active_metrics["accuracy"] or 0), 2)
        precision = round(float(active_metrics["precision_score"] or 0), 4)
        recall = round(float(active_metrics["recall_score"] or 0), 4)
        f1_score_value = round(float(active_metrics["f1_score"] or 0), 4)
        roc_auc = round(float(active_metrics["roc_auc"] or 0), 4) if active_metrics["roc_auc"] is not None else None
        pr_auc = round(float(active_metrics["pr_auc"] or 0), 4) if active_metrics["pr_auc"] is not None else None
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

    all_model_results = [
        build_model_item(
            model["id"],
            metrics_by_id[model["id"]],
            active_model_id,
            dataset_id,
            has_labels,
        )
        for model in UNSUPERVISED_MODELS + SUPERVISED_MODELS
    ]

    response = {
        "currentModel": active_model_name,
        "activeModelId": active_model_id,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1Score": f1_score_value,
        "rocAuc": roc_auc,
        "prAuc": pr_auc,
        "fpr": fpr,
        "fnr": fnr,
        "modelScore": active_model_score,
        "evaluationMode": active_evaluation_mode,
        "datasetHasLabels": has_labels,
        "hasLabels": has_labels,
        "totalRecords": int(active_metrics["total_records"] or 0),
        "totalAnomalies": int(active_metrics["total_anomalies"] or 0),
        "anomalyRate": active_anomaly_rate,
        "trueAnomalies": active_metrics.get("true_anomalies"),
        "scoreMean": active_metrics.get("score_mean"),
        "scoreStd": active_metrics.get("score_std"),
        "scoreVariance": active_metrics.get("score_variance"),
        "trainingTimeSeconds": active_metrics.get("training_time_seconds"),
        "predictionTimeSeconds": active_metrics.get("prediction_time_seconds"),
        "source": "Model metrics loaded from PostgreSQL model_metrics table.",
        "availableModels": build_available_models(has_labels),
        "selectedModels": {
            "modelA": selected_model_a,
            "modelB": selected_model_b,
        },
        "confusionMatrix": confusion_matrix,
        "comparison": comparison,
        "allModelResults": all_model_results,
        "groups": {
            "unsupervised": [model["id"] for model in UNSUPERVISED_MODELS],
            "supervised": [model["id"] for model in SUPERVISED_MODELS],
            "future": [model["id"] for model in FUTURE_MODELS],
        },
    }

    if active_metrics["created_at"]:
        response["lastTrainedAt"] = active_metrics["created_at"].strftime("%Y-%m-%d %H:%M:%S")

    return response