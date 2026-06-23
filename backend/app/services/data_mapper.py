from typing import Optional

import pandas as pd

from app.services.settings_service import get_threshold


def _find_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    normalized = {column.lower().strip(): column for column in df.columns}

    for candidate in candidates:
        key = candidate.lower().strip()
        if key in normalized:
            return normalized[key]

    return None


def _to_boolean_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)

    normalized = series.astype(str).str.lower().str.strip()

    return normalized.isin([
        "1",
        "true",
        "yes",
        "y",
        "anomaly",
        "anomalous",
    ])
def _clean_text_series(series: pd.Series, fallback: str) -> pd.Series:
    cleaned = series.astype(str).str.strip()

    cleaned = cleaned.replace({
        "": fallback,
        "nan": fallback,
        "NaN": fallback,
        "None": fallback,
        "null": fallback,
        "NULL": fallback,
    })

    return cleaned.fillna(fallback)

def map_to_standard_measurements(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Pretvara CSV u standardni format aplikacije.

    Vazno:
    - isAnomaly je trenutni detection output koji frontend prikazuje.
    - groundTruthAnomaly se cuva samo interno za racunanje metrika modela.
    - Kada stigne pravi ML deo, isAnomaly/anomalyScore mogu da dolaze iz ML rezultata.
    """
    df = raw_df.copy()
    threshold = get_threshold()

    timestamp_col = _find_column(df, [
        "timestamp", "time", "datetime", "date_time", "date", "measurement_time"
    ])

    radiation_col = _find_column(df, [
        "radiation_uSv_h", "radiation", "radiation_level", "dose_rate", "value", "measurement"
    ])

    sensor_col = _find_column(df, [
        "sensor_id", "sensor", "sensor_name", "detector", "detector_id", "device", "device_id", "instrument", "instrument_id", "station", "station_id", "channel",
    ])

    location_col = _find_column(df, [
        "location", "place", "room", "site"
    ])

    temperature_col = _find_column(df, [
        "temperature_c", "temperature", "temp", "temp_c"
    ])

    humidity_col = _find_column(df, [
        "humidity_percent", "humidity", "rh", "relative_humidity"
    ])

    anomaly_type_col = _find_column(df, [
        "anomaly_type", "type", "event_type"
    ])

    ground_truth_col = _find_column(df, [
        "is_anomaly", "ground_truth", "ground_truth_anomaly", "label", "target"
    ])

    if timestamp_col is None:
        raise ValueError("CSV mora da ima timestamp/datetime kolonu.")

    if radiation_col is None:
        raise ValueError("CSV mora da ima kolonu za nivo zracenja/dose rate.")

    working_df = pd.DataFrame()

    working_df["timestamp"] = pd.to_datetime(df[timestamp_col], errors="coerce")
    working_df["radiationLevel"] = pd.to_numeric(df[radiation_col], errors="coerce")

    working_df["sensorId"] = (_clean_text_series(df[sensor_col], "Unknown sensor")if sensor_col else "Unknown sensor")
    working_df["location"] = (_clean_text_series(df[location_col], "Unknown location") if location_col else "Unknown location")

    working_df["temperature"] = (
        pd.to_numeric(df[temperature_col], errors="coerce")
        if temperature_col
        else None
    )

    working_df["humidity"] = (
        pd.to_numeric(df[humidity_col], errors="coerce")
        if humidity_col
        else None
    )

    if anomaly_type_col:
        working_df["originalAnomalyType"] = df[anomaly_type_col].astype(str)
    else:
        working_df["originalAnomalyType"] = "threshold_detection"

    if ground_truth_col:
        working_df["groundTruthAnomaly"] = _to_boolean_series(df[ground_truth_col])
    else:
        working_df["groundTruthAnomaly"] = pd.NA

    working_df = working_df.dropna(subset=["timestamp", "radiationLevel"]).reset_index(drop=True)

    result = pd.DataFrame()

    result["timestamp"] = working_df["timestamp"]
    result["radiationLevel"] = working_df["radiationLevel"]
    result["sensorId"] = working_df["sensorId"]
    result["location"] = working_df["location"]
    result["temperature"] = working_df["temperature"]
    result["humidity"] = working_df["humidity"]

    result["isAnomaly"] = result["radiationLevel"] > threshold
    result["groundTruthAnomaly"] = working_df["groundTruthAnomaly"]

    result["anomalyType"] = "normal"

    result.loc[
        result["isAnomaly"],
        "anomalyType"
    ] = working_df.loc[
        result["isAnomaly"],
        "originalAnomalyType"
    ].replace("normal", "threshold_detection")

    if threshold > 0:
        distance_from_threshold = ((result["radiationLevel"] - threshold) / threshold).clip(lower=0)
    else:
        distance_from_threshold = result["radiationLevel"].clip(lower=0)

    max_distance = distance_from_threshold.max()

    if max_distance and max_distance > 0:
        result["anomalyScore"] = (distance_from_threshold / max_distance).round(3)
    else:
        result["anomalyScore"] = 0.0

    result["status"] = result.apply(lambda row: _status_from_row(row, threshold), axis=1)

    result = result.sort_values("timestamp").reset_index(drop=True)

    return result


def _status_from_row(row, threshold: float) -> str:
    if not bool(row["isAnomaly"]):
        return "Normal"

    value = float(row["radiationLevel"])

    if threshold > 0 and value >= threshold * 2:
        return "Critical"

    return "High"