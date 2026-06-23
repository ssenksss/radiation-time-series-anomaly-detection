import pandas as pd
from app.services.settings_service import get_threshold

def calculate_summary(df: pd.DataFrame) -> dict:
    latest = df.iloc[-1]
    threshold = get_threshold()

    return {
        "datasetName": "mock_radiation_measurements.csv",
        "totalMeasurements": int(len(df)),
        "totalAnomalies": int(df["isAnomaly"].sum()),
        "currentLevel": round(float(latest["radiationLevel"]), 4),
        "averageLevel": round(float(df["radiationLevel"].mean()), 4),
        "maxLevel": round(float(df["radiationLevel"].max()), 4),
        "minLevel": round(float(df["radiationLevel"].min()), 4),
        "threshold": threshold,
        "activeAlert": bool(latest["isAnomaly"]),
        "lastUpdated": latest["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
    }