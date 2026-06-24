from app.database.connection import fetch_one, execute_query


VALID_MODEL_IDS = {"isolation_forest", "lof", "rnn"}


def get_setting(key: str, default_value: str) -> str:
    row = fetch_one(
        """
        SELECT value
        FROM app_settings
        WHERE key = %s;
        """,
        (key,),
    )

    if not row:
        return default_value

    return str(row["value"])


def normalize_model_id(model_id: str) -> str:
    normalized = model_id.strip().lower().replace("-", "_").replace(" ", "_")

    aliases = {
        "isolation_forest": "isolation_forest",
        "isolationforest": "isolation_forest",
        "isolation": "isolation_forest",
        "iforest": "isolation_forest",

        "local_outlier_factor": "lof",
        "lof": "lof",

        "recurrent_neural_network": "rnn",
        "rnn": "rnn",
    }

    resolved = aliases.get(normalized, normalized)

    if resolved in VALID_MODEL_IDS:
        return resolved

    return "isolation_forest"


def get_settings_from_database() -> dict:
    threshold = float(get_setting("threshold", "0.18"))
    active_model = normalize_model_id(get_setting("active_model", "isolation_forest"))
    active_dataset_id = int(get_setting("active_dataset_id", "1"))

    return {
        "threshold": threshold,
        "activeModel": active_model,
        "activeDatasetId": active_dataset_id,
        "notificationsEnabled": True,
        "emailAlertsEnabled": True,
        "email": "alerts@mail.com",
    }


def update_threshold_in_database(threshold: float) -> dict:
    threshold = float(threshold)

    if threshold < 0:
        raise ValueError("Threshold must be greater than or equal to 0.")

    if threshold > 10:
        raise ValueError("Threshold is too high for this prototype.")

    execute_query(
        """
        INSERT INTO app_settings (key, value)
        VALUES ('threshold', %s)
        ON CONFLICT (key) DO UPDATE
        SET value = EXCLUDED.value,
            updated_at = CURRENT_TIMESTAMP;
        """,
        (str(round(threshold, 4)),),
    )

    return get_settings_from_database()


def update_active_model_in_database(model_id: str) -> dict:
    normalized_model_id = normalize_model_id(model_id)

    execute_query(
        """
        INSERT INTO app_settings (key, value)
        VALUES ('active_model', %s)
        ON CONFLICT (key) DO UPDATE
        SET value = EXCLUDED.value,
            updated_at = CURRENT_TIMESTAMP;
        """,
        (normalized_model_id,),
    )

    return get_settings_from_database()