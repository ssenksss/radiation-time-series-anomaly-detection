import pandas as pd
from typing import Optional

AVAILABLE_MODELS = {
    "threshold": {
        "id": "threshold",
        "name": "Threshold Detection",
        "status": "implemented",
    },
    "isolation_forest": {
        "id": "isolation_forest",
        "name": "Isolation Forest",
        "status": "pending",
    },
    "lof": {
        "id": "lof",
        "name": "Local Outlier Factor",
        "status": "pending",
    },
}

DEFAULT_MODEL_A = "threshold"
DEFAULT_MODEL_B = "isolation_forest"


def _safe_divide(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0

    return numerator / denominator


def _round_metric(value: float) -> float:
    return round(float(value), 3)


def _round_percent(value: float) -> float:
    return round(float(value) * 100, 1)


def _get_model_name(model_id: str) -> str:
    model = AVAILABLE_MODELS.get(model_id)

    if not model:
        return model_id

    return model["name"]


def _normalize_model_id(model_id: Optional[str]) -> str:
    if not model_id:
        return DEFAULT_MODEL_A

    normalized = model_id.strip().lower().replace("-", "_").replace(" ", "_")

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

    return aliases.get(normalized, DEFAULT_MODEL_A)


def _resolve_selected_models(model_a: Optional[str], model_b: Optional[str]) -> tuple:
    resolved_a = _normalize_model_id(model_a)
    resolved_b = _normalize_model_id(model_b)

    if resolved_a not in AVAILABLE_MODELS:
        resolved_a = DEFAULT_MODEL_A

    if resolved_b not in AVAILABLE_MODELS:
        resolved_b = DEFAULT_MODEL_B

    if resolved_a == resolved_b:
        resolved_b = DEFAULT_MODEL_B if resolved_a != DEFAULT_MODEL_B else "lof"

    return resolved_a, resolved_b


def _build_pending_model(model_id: str) -> dict:
    model = AVAILABLE_MODELS.get(model_id, {
        "id": model_id,
        "name": model_id,
        "status": "pending",
    })

    return {
        "id": model["id"],
        "model": model["name"],
        "score": 0,
        "accuracy": None,
        "precision": None,
        "recall": None,
        "fpr": None,
        "fnr": None,
        "active": False,
        "status": "Pending ML implementation",
    }


def _calculate_confusion_matrix_metrics(df: pd.DataFrame) -> dict:
    total = int(len(df))

    if total == 0:
        return {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "fpr": 0.0,
            "fnr": 0.0,
            "tp": 0,
            "tn": 0,
            "fp": 0,
            "fn": 0,
            "detected_anomalies": 0,
            "evaluation_note": "Dataset is empty",
        }

    predicted = df["isAnomaly"].fillna(False).astype(bool)
    detected_anomalies = int(predicted.sum())

    has_ground_truth = (
            "groundTruthAnomaly" in df.columns
            and df["groundTruthAnomaly"].notna().any()
    )

    if has_ground_truth:
        actual = df["groundTruthAnomaly"].fillna(False).astype(bool)

        tp = int((predicted & actual).sum())
        tn = int((~predicted & ~actual).sum())
        fp = int((predicted & ~actual).sum())
        fn = int((~predicted & actual).sum())

        accuracy = _round_percent(_safe_divide(tp + tn, total))
        precision = _round_metric(_safe_divide(tp, tp + fp))
        recall = _round_metric(_safe_divide(tp, tp + fn))
        fpr = _round_metric(_safe_divide(fp, fp + tn))
        fnr = _round_metric(_safe_divide(fn, fn + tp))

        evaluation_note = "Compared with CSV ground-truth labels"
    else:
        tp = detected_anomalies
        tn = total - detected_anomalies
        fp = 0
        fn = 0

        accuracy = 0.0
        precision = 0.0
        recall = 0.0
        fpr = 0.0
        fnr = 0.0

        evaluation_note = "Ground-truth labels not available"

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "fpr": fpr,
        "fnr": fnr,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "detected_anomalies": detected_anomalies,
        "evaluation_note": evaluation_note,
    }


def _build_threshold_model(df: pd.DataFrame) -> dict:
    metrics = _calculate_confusion_matrix_metrics(df)

    return {
        "id": "threshold",
        "model": "Threshold Detection",
        "score": metrics["accuracy"],
        "accuracy": metrics["accuracy"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "fpr": metrics["fpr"],
        "fnr": metrics["fnr"],
        "active": True,
        "status": "Computed",
    }


def _build_model_result(df: pd.DataFrame, model_id: str) -> dict:
    if model_id == "threshold":
        return _build_threshold_model(df)

    if model_id == "isolation_forest":
        return _build_pending_model("isolation_forest")

    if model_id == "lof":
        return _build_pending_model("lof")

    return _build_pending_model(model_id)


def get_model_info(
        df: pd.DataFrame,
        model_a: Optional[str] = DEFAULT_MODEL_A,
        model_b: Optional[str] = DEFAULT_MODEL_B,
) -> dict:
    """
    Vraca informacije za Model Testing panel.

    Trenutno:
    - Threshold Detection je implementiran i racuna stvarne metrike.
    - Isolation Forest i LOF postoje kao opcije, ali su pending dok ne krene ML faza.

    Ideja:
    - korisnik bira dva modela za poredjenje
    - frontend salje modelA i modelB
    - backend vraca comparison samo za ta dva modela

    Kasnije u ML fazi:
    - u _build_model_result se dodaje prava logika za Isolation Forest i LOF
    """

    selected_model_a, selected_model_b = _resolve_selected_models(model_a, model_b)

    metrics = _calculate_confusion_matrix_metrics(df)
    total = int(len(df))

    comparison = [
        _build_model_result(df, selected_model_a),
        _build_model_result(df, selected_model_b),
    ]

    primary_result = comparison[0]

    primary_accuracy = primary_result.get("accuracy")
    primary_precision = primary_result.get("precision")
    primary_fpr = primary_result.get("fpr")
    primary_fnr = primary_result.get("fnr")

    return {
        "currentModel": _get_model_name(selected_model_a),
        "accuracy": primary_accuracy if primary_accuracy is not None else 0.0,
        "precision": primary_precision if primary_precision is not None else 0.0,
        "fpr": primary_fpr if primary_fpr is not None else 0.0,
        "fnr": primary_fnr if primary_fnr is not None else 0.0,
        "source": (
            f"{metrics['evaluation_note']} - "
            f"{total} measurements - "
            f"{metrics['detected_anomalies']} detected anomalies"
        ),
        "availableModels": list(AVAILABLE_MODELS.values()),
        "selectedModels": {
            "modelA": selected_model_a,
            "modelB": selected_model_b,
        },
        "confusionMatrix": {
            "tp": metrics["tp"],
            "tn": metrics["tn"],
            "fp": metrics["fp"],
            "fn": metrics["fn"],
        },
        "comparison": comparison,
    }