from pathlib import Path
import re
import unicodedata
from typing import Optional

import pandas as pd


STANDARD_COLUMNS = [
    "timestamp",
    "radiation_uSv_h",
    "sensor_id",
    "location",
    "temperature_c",
    "humidity_percent",
    "is_anomaly",
    "anomaly_type",
]


COLUMN_ALIASES = {
    "timestamp": [
        "timestamp",
        "time",
        "datetime",
        "date_time",
        "date",
        "measurement_time",
        "created_at",
        "vreme",
        "vrijeme",
        "datum",
        "datum_vreme",
        "datum_vrijeme",
    ],
    "radiation": [
        "radiation",
        "radiation_level",
        "radiation_usv_h",
        "radiation_uSv_h",
        "radiation_µsv_h",
        "radiation_microsievert",
        "dose",
        "dose_rate",
        "dose_rate_usv_h",
        "gamma",
        "rad",
        "value",
        "level",
        "measurement",
        "nsv_h",
        "usv_h",
        "µsv_h",
    ],
    "unit": [
        "unit",
        "units",
        "jedinica",
        "measurement_unit",
    ],
    "sensor_id": [
        "sensor_id",
        "sensor",
        "device",
        "device_id",
        "station",
        "station_id",
        "detector",
        "instrument",
        "merna_stanica",
    ],
    "location": [
        "location",
        "lokacija",
        "place",
        "site",
        "station_name",
        "city",
        "grad",
        "room",
    ],
    "temperature": [
        "temperature",
        "temperature_c",
        "temp",
        "temp_c",
        "t",
    ],
    "humidity": [
        "humidity",
        "humidity_percent",
        "relative_humidity",
        "rhum",
        "rh",
        "vlaznost",
        "vlažnost",
    ],
    "is_anomaly": [
        "is_anomaly",
        "anomaly",
        "label",
        "target",
        "outlier",
        "is_outlier",
    ],
    "anomaly_type": [
        "anomaly_type",
        "type",
        "event_type",
        "status_type",
    ],
}


def normalize_text(value: object) -> str:
    text = str(value).strip().lower()

    text = unicodedata.normalize("NFKD", text)
    text = "".join(character for character in text if not unicodedata.combining(character))

    replacements = {
        " ": "_",
        "-": "_",
        ".": "_",
        "(": "",
        ")": "",
        "[": "",
        "]": "",
        "/": "_",
        "\\": "_",
        "µ": "u",
        "μ": "u",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    while "__" in text:
        text = text.replace("__", "_")

    return text.strip("_")


def read_csv_flexible(csv_path: Path) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-8", "cp1250", "latin1"]
    last_error: Optional[Exception] = None

    for encoding in encodings:
        try:
            return pd.read_csv(
                csv_path,
                sep=None,
                engine="python",
                encoding=encoding,
                dtype=str,
            )
        except Exception as error:
            last_error = error

    raise RuntimeError(f"CSV file could not be read. Last error: {last_error}")


def find_column(dataframe: pd.DataFrame, aliases: list[str]) -> Optional[str]:
    normalized_columns = {
        normalize_text(column): column
        for column in dataframe.columns
    }

    normalized_aliases = [normalize_text(alias) for alias in aliases]

    for alias in normalized_aliases:
        if alias in normalized_columns:
            return normalized_columns[alias]

    for normalized_column, original_column in normalized_columns.items():
        for alias in normalized_aliases:
            if alias and alias in normalized_column:
                return original_column

    return None


def clean_numeric_series(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.strip()
        .str.replace("\u00a0", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    cleaned = cleaned.replace(
        {
            "": None,
            "nan": None,
            "None": None,
            "NULL": None,
            "null": None,
            "-": None,
        }
    )

    return pd.to_numeric(cleaned, errors="coerce")


def detect_unit(dataframe: pd.DataFrame, unit_column: Optional[str], radiation_column: str) -> str:
    if unit_column and unit_column in dataframe.columns:
        values = dataframe[unit_column].dropna().astype(str).str.strip()

        if not values.empty:
            return normalize_text(values.mode().iloc[0])

    radiation_column_normalized = normalize_text(radiation_column)

    if "nsv" in radiation_column_normalized:
        return "nsv_h"

    if "msv" in radiation_column_normalized:
        return "msv_h"

    return "usv_h"


def convert_radiation_to_usv(series: pd.Series, unit: str) -> pd.Series:
    values = clean_numeric_series(series)

    normalized_unit = normalize_text(unit)

    if "nsv" in normalized_unit:
        return values / 1000.0

    if "msv" in normalized_unit:
        return values * 1000.0

    return values


def normalize_boolean(value: object) -> str:
    if value is None or pd.isna(value):
        return ""

    text = str(value).strip().lower()

    if text in {"1", "true", "yes", "y", "da", "anomaly", "outlier"}:
        return "1"

    if text in {"0", "false", "no", "n", "ne", "normal"}:
        return "0"

    return ""


def clean_name_from_filename(path: Path) -> str:
    stem = path.stem.replace("_", " ").replace("-", " ").strip()

    # Uploaded files are saved as YYYYMMDD_HHMMSS_original_name.csv.
    # ZIP members can also be extracted as 001_original_name.csv.
    # These technical prefixes should never become sensor IDs in the UI.
    stem = re.sub(r"^\d{8}\s+\d{6}\s+", "", stem)
    stem = re.sub(r"^\d{3}\s+", "", stem)
    stem = re.sub(r"\s+", " ", stem).strip()

    return stem or "Radiation sensor"


def remove_repeated_header_rows(dataframe: pd.DataFrame, timestamp_column: Optional[str]) -> pd.DataFrame:
    cleaned = dataframe.copy()

    if timestamp_column and timestamp_column in cleaned.columns:
        timestamp_column_normalized = normalize_text(timestamp_column)

        cleaned = cleaned[
            cleaned[timestamp_column].astype(str).apply(normalize_text) != timestamp_column_normalized
            ]

        cleaned = cleaned[
            cleaned[timestamp_column].astype(str).apply(normalize_text) != "time"
            ]

    return cleaned.reset_index(drop=True)


def standardize_radiation_csv(csv_path: Path) -> pd.DataFrame:
    raw = read_csv_flexible(csv_path)

    if raw.empty:
        raise RuntimeError("CSV file is empty.")

    timestamp_column = find_column(raw, COLUMN_ALIASES["timestamp"])
    radiation_column = find_column(raw, COLUMN_ALIASES["radiation"])

    if not timestamp_column:
        raise RuntimeError(
            "Could not detect timestamp column. Expected one of: "
            + ", ".join(COLUMN_ALIASES["timestamp"])
        )

    if not radiation_column:
        raise RuntimeError(
            "Could not detect radiation value column. Expected one of: "
            + ", ".join(COLUMN_ALIASES["radiation"])
        )

    raw = remove_repeated_header_rows(raw, timestamp_column)

    unit_column = find_column(raw, COLUMN_ALIASES["unit"])
    sensor_column = find_column(raw, COLUMN_ALIASES["sensor_id"])
    location_column = find_column(raw, COLUMN_ALIASES["location"])
    temperature_column = find_column(raw, COLUMN_ALIASES["temperature"])
    humidity_column = find_column(raw, COLUMN_ALIASES["humidity"])
    label_column = find_column(raw, COLUMN_ALIASES["is_anomaly"])
    anomaly_type_column = find_column(raw, COLUMN_ALIASES["anomaly_type"])

    detected_unit = detect_unit(raw, unit_column, radiation_column)

    location_from_filename = clean_name_from_filename(csv_path)
    sensor_from_filename = location_from_filename.upper().replace(" ", "_")

    standardized = pd.DataFrame()

    standardized["timestamp"] = raw[timestamp_column].astype(str).str.strip()
    standardized["radiation_uSv_h"] = convert_radiation_to_usv(raw[radiation_column], detected_unit)

    if sensor_column:
        standardized["sensor_id"] = raw[sensor_column].astype(str).str.strip()
    else:
        standardized["sensor_id"] = sensor_from_filename

    if location_column:
        standardized["location"] = raw[location_column].astype(str).str.strip()
    else:
        standardized["location"] = location_from_filename

    if temperature_column:
        standardized["temperature_c"] = clean_numeric_series(raw[temperature_column])
    else:
        standardized["temperature_c"] = None

    if humidity_column:
        standardized["humidity_percent"] = clean_numeric_series(raw[humidity_column])
    else:
        standardized["humidity_percent"] = None

    if label_column:
        standardized["is_anomaly"] = raw[label_column].apply(normalize_boolean)
    else:
        standardized["is_anomaly"] = ""

    if anomaly_type_column:
        standardized["anomaly_type"] = raw[anomaly_type_column].astype(str).str.strip()
    else:
        standardized["anomaly_type"] = "normal"

    standardized["timestamp_parsed"] = pd.to_datetime(
        standardized["timestamp"],
        errors="coerce",
        dayfirst=False,
    )

    standardized = standardized.dropna(subset=["timestamp_parsed", "radiation_uSv_h"])

    standardized["timestamp"] = standardized["timestamp_parsed"].dt.strftime("%Y-%m-%d %H:%M:%S")
    standardized = standardized.drop(columns=["timestamp_parsed"])

    standardized["radiation_uSv_h"] = standardized["radiation_uSv_h"].round(6)

    standardized = standardized[STANDARD_COLUMNS]
    standardized = standardized.reset_index(drop=True)

    if standardized.empty:
        raise RuntimeError(
            "CSV was read, but no valid rows remained after cleaning. "
            "Check timestamp and radiation columns."
        )

    return standardized