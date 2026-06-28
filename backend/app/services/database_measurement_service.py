from app.database.connection import fetch_one, fetch_all


MODEL_ID_TO_NAME = {
    "isolation_forest": "Isolation Forest",
    "lof": "Local Outlier Factor",
    "one_class_svm": "One-Class SVM",
    "elliptic_envelope": "Elliptic Envelope",
    "dbscan": "DBSCAN",
    "kmeans_distance": "K-Means Distance",
    "gaussian_mixture": "Gaussian Mixture Model",
    "pca_reconstruction": "PCA Reconstruction Error",
    "hbos": "HBOS",
    "ecod": "ECOD",
    "logistic_regression": "Logistic Regression",
    "decision_tree": "Decision Tree",
    "random_forest": "Random Forest",
    "gradient_boosting": "Gradient Boosting",
    "knn_classifier": "KNN Classifier",
    "rnn": "Recurrent Neural Network",
}


def normalize_model_id(model_id: str) -> str:
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

    if resolved in MODEL_ID_TO_NAME:
        return resolved

    return "isolation_forest"


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


def get_active_model_name() -> str:
    row = fetch_one(
        """
        SELECT value
        FROM app_settings
        WHERE key = 'active_model';
        """
    )

    if not row:
        return "Isolation Forest"

    model_id = normalize_model_id(str(row["value"]))
    return MODEL_ID_TO_NAME.get(model_id, "Isolation Forest")


def get_threshold() -> float:
    row = fetch_one(
        """
        SELECT value
        FROM app_settings
        WHERE key = 'threshold';
        """
    )

    if not row:
        return 0.18

    return float(row["value"])


def classify_radiation_event(radiation_level: float, threshold: float) -> tuple[str, str]:
    if threshold <= 0:
        return "normal", "Normal"

    if radiation_level < threshold:
        return "normal", "Normal"

    if radiation_level >= threshold * 2:
        return "spike", "Critical"

    return "warning", "High"


def get_measurements_from_database(limit: int = 1000) -> list:
    dataset_id = get_active_dataset_id()
    threshold = get_threshold()
    active_model_name = get_active_model_name()

    rows = fetch_all(
        """
        SELECT *
        FROM (
            SELECT
                ar.timestamp,
                ar.radiation_level,
                ar.predicted_anomaly,
                ar.anomaly_score,
                ar.status AS ml_status,
                cm.sensor_id,
                cm.location,
                cm.temperature,
                cm.humidity,
                cm.anomaly_type
            FROM anomaly_results ar
            JOIN feature_measurements fm
                ON ar.feature_measurement_id = fm.id
            JOIN clean_measurements cm
                ON fm.clean_measurement_id = cm.id
            WHERE ar.dataset_id = %s
              AND ar.model_name = %s
            ORDER BY ar.timestamp DESC
            LIMIT %s
        ) latest_rows
        ORDER BY timestamp ASC;
        """,
        (dataset_id, active_model_name, limit),
    )

    measurements = []

    for row in rows:
        radiation_level = float(row["radiation_level"])
        anomaly_type, status = classify_radiation_event(radiation_level, threshold)
        is_visible_anomaly = bool(row["predicted_anomaly"]) and radiation_level >= threshold

        measurements.append(
            {
                "timestamp": row["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "radiationLevel": round(radiation_level, 4),
                "sensorId": str(row["sensor_id"]),
                "location": str(row["location"]),
                "temperature": None if row["temperature"] is None else round(float(row["temperature"]), 2),
                "humidity": None if row["humidity"] is None else round(float(row["humidity"]), 2),
                "isAnomaly": is_visible_anomaly,
                "anomalyScore": round(float(row["anomaly_score"]), 4),
                "anomalyType": anomaly_type,
                "status": status,
            }
        )

    return measurements