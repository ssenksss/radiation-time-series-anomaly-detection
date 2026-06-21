import pandas as pd


def get_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["isAnomaly"] == True].copy().sort_values("timestamp", ascending=False)