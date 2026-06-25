from app.database.connection import fetch_one


MODEL_ID_TO_NAME = {
    "isolation_forest": "Isolation Forest",
    "lof": "Local Outlier Factor",
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

        "recurrent_neural_network": "rnn",
        "rnn": "rnn",
    }

    return aliases.get(normalized, "isolation_forest")


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


def get_summary_from_database() -> dict:
    dataset_id = get_active_dataset_id()
    threshold = get_threshold()
    active_model_name = get_active_model_name()

    summary_row = fetch_one(
        """
        SELECT
            d.name AS dataset_name,
            COUNT(ar.id) AS total_measurements,
            COALESCE(
                SUM(
                    CASE
                        WHEN ar.predicted_anomaly = TRUE
                         AND ar.radiation_level >= %s
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS total_anomalies,
            COALESCE(AVG(ar.radiation_level), 0) AS average_level,
            COALESCE(MAX(ar.radiation_level), 0) AS max_level,
            COALESCE(MIN(ar.radiation_level), 0) AS min_level,
            MAX(ar.timestamp) AS last_updated
        FROM datasets d
        LEFT JOIN anomaly_results ar
            ON ar.dataset_id = d.id
           AND ar.model_name = %s
        WHERE d.id = %s
        GROUP BY d.name;
        """,
        (threshold, active_model_name, dataset_id),
    )

    latest_row = fetch_one(
        """
        SELECT
            radiation_level,
            predicted_anomaly,
            timestamp
        FROM anomaly_results
        WHERE dataset_id = %s
          AND model_name = %s
        ORDER BY timestamp DESC
        LIMIT 1;
        """,
        (dataset_id, active_model_name),
    )

    if not summary_row:
        return {
            "datasetName": "No active dataset",
            "totalMeasurements": 0,
            "totalAnomalies": 0,
            "currentLevel": 0,
            "averageLevel": 0,
            "maxLevel": 0,
            "minLevel": 0,
            "threshold": threshold,
            "activeAlert": False,
            "lastUpdated": "",
        }

    current_level = 0
    active_alert = False
    last_updated = ""

    if latest_row:
        current_level = float(latest_row["radiation_level"])
        active_alert = bool(latest_row["predicted_anomaly"]) and current_level >= threshold
        last_updated = latest_row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

    if summary_row["last_updated"]:
        last_updated = summary_row["last_updated"].strftime("%Y-%m-%d %H:%M:%S")

    return {
        "datasetName": summary_row["dataset_name"],
        "totalMeasurements": int(summary_row["total_measurements"]),
        "totalAnomalies": int(summary_row["total_anomalies"]),
        "currentLevel": round(current_level, 4),
        "averageLevel": round(float(summary_row["average_level"]), 4),
        "maxLevel": round(float(summary_row["max_level"]), 4),
        "minLevel": round(float(summary_row["min_level"]), 4),
        "threshold": round(threshold, 4),
        "activeAlert": active_alert,
        "lastUpdated": last_updated,
    }