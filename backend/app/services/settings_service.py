import json
from app.utils.paths import DATA_DIR

SETTINGS_PATH = DATA_DIR / "settings.json"

AVAILABLE_ACTIVE_MODELS = {
    "threshold",
    "isolation_forest",
    "lof",
}

DEFAULT_SETTINGS = {
    "threshold": 0.18,
    "activeModel": "threshold",
}


def _ensure_settings_file() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not SETTINGS_PATH.exists():
        save_settings(DEFAULT_SETTINGS)


def get_settings() -> dict:
    _ensure_settings_file()

    with open(SETTINGS_PATH, "r", encoding="utf-8") as file:
        settings = json.load(file)

    merged_settings = {
        **DEFAULT_SETTINGS,
        **settings,
    }

    if merged_settings.get("activeModel") not in AVAILABLE_ACTIVE_MODELS:
        merged_settings["activeModel"] = DEFAULT_SETTINGS["activeModel"]

    return merged_settings


def save_settings(settings: dict) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    normalized_settings = {
        **DEFAULT_SETTINGS,
        **settings,
    }

    with open(SETTINGS_PATH, "w", encoding="utf-8") as file:
        json.dump(normalized_settings, file, indent=2)

    return normalized_settings


def get_threshold() -> float:
    settings = get_settings()
    return float(settings.get("threshold", DEFAULT_SETTINGS["threshold"]))


def get_active_model() -> str:
    settings = get_settings()
    return str(settings.get("activeModel", DEFAULT_SETTINGS["activeModel"]))


def update_threshold(new_threshold: float) -> dict:
    if new_threshold < 0:
        raise ValueError("Threshold must be greater than or equal to 0.")

    if new_threshold > 10:
        raise ValueError("Threshold is too high for this prototype.")

    settings = get_settings()
    settings["threshold"] = round(float(new_threshold), 4)

    return save_settings(settings)


def update_active_model(active_model: str) -> dict:
    normalized_model = active_model.strip().lower().replace("-", "_").replace(" ", "_")

    aliases = {
        "threshold_detection": "threshold",
        "threshold": "threshold",
        "baseline": "threshold",

        "isolationforest": "isolation_forest",
        "isolation_forest": "isolation_forest",
        "isolation": "isolation_forest",

        "local_outlier_factor": "lof",
        "lof": "lof",
    }

    resolved_model = aliases.get(normalized_model, normalized_model)

    if resolved_model not in AVAILABLE_ACTIVE_MODELS:
        raise ValueError("Selected model is not supported.")

    settings = get_settings()
    settings["activeModel"] = resolved_model

    return save_settings(settings)