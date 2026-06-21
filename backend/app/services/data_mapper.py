import pandas as pd

DEFAULT_THRESHOLD = 0.18


from typing import Optional
import pandas as pd

DEFAULT_THRESHOLD = 0.18


def _find_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    normalized = {column.lower().strip(): column for column in df.columns}

    for candidate in candidates:
        key = candidate.lower().strip()
        if key in normalized:
            return normalized[key]

    return None


def map_to_standard_measurements(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Pretvara bilo koji CSV format u standardni format aplikacije.

    Frontend i API uvek rade sa ovim kolonama:
    timestamp, radiationLevel, sensorId, location, temperature, humidity,
    isAnomaly, anomalyType, anomalyScore, status

    Kada stigne realni CSV, ovde dodajemo nova imena kolona u candidates liste.
    """
    df = raw_df.copy()

    timestamp_col = _find_column(df, [
        "timestamp", "time", "datetime", "date_time", "date", "measurement_time"
    ])

    radiation_col = _find_column(df, [
        "radiation_uSv_h", "radiation", "radiation_level", "dose_rate", "value", "measurement"
    ])

    sensor_col = _find_column(df, [
        "sensor_id", "sensor", "device", "device_id", "station_id"
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

    is_anomaly_col = _find_column(df, [
        "is_anomaly", "anomaly", "label", "target"
    ])

    anomaly_type_col = _find_column(df, [
        "anomaly_type", "type", "event_type"
    ])

    if timestamp_col is None:
        raise ValueError("CSV mora da ima timestamp/datetime kolonu.")

    if radiation_col is None:
        raise ValueError("CSV mora da ima kolonu za nivo zracenja/dose rate.")

    result = pd.DataFrame()

    result["timestamp"] = pd.to_datetime(df[timestamp_col], errors="coerce")
    result["radiationLevel"] = pd.to_numeric(df[radiation_col], errors="coerce")

    result = result.dropna(subset=["timestamp", "radiationLevel"]).reset_index(drop=True)

    result["sensorId"] = df[sensor_col].astype(str) if sensor_col else "RAD-001"
    result["location"] = df[location_col].astype(str) if location_col else "Unknown location"

    result["temperature"] = (
        pd.to_numeric(df[temperature_col], errors="coerce")
        if temperature_col
        else None
    )

    result["humidity"] = (
        pd.to_numeric(df[humidity_col], errors="coerce")
        if humidity_col
        else None
    )

    if is_anomaly_col:
        result["isAnomaly"] = df[is_anomaly_col].astype(bool)
    else:
        result["isAnomaly"] = result["radiationLevel"] > DEFAULT_THRESHOLD

    result["anomalyType"] = df[anomaly_type_col].astype(str) if anomaly_type_col else "threshold_detection"
    result.loc[~result["isAnomaly"], "anomalyType"] = "normal"

    # Privremeni anomaly score dok ne dodje pravi ML deo.
    # Vrednost raste sto je nivo zracenja dalje iznad proseka.
    mean_value = result["radiationLevel"].mean()
    std_value = result["radiationLevel"].std() or 1

    z_score = ((result["radiationLevel"] - mean_value) / std_value).clip(lower=0)
    result["anomalyScore"] = (z_score / (z_score.max() or 1)).round(3)

    result["status"] = result.apply(_status_from_row, axis=1)

    result = result.sort_values("timestamp").reset_index(drop=True)

    return result


def _status_from_row(row) -> str:
    if not bool(row["isAnomaly"]):
        return "Normal"

    value = float(row["radiationLevel"])

    if value >= 0.35:
        return "Critical"

    if value >= DEFAULT_THRESHOLD:
        return "High"

    return "Anomaly"