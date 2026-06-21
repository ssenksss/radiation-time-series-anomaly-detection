import pandas as pd


def get_model_info(df: pd.DataFrame) -> dict:
    """
    Privremeni model-info dok ne uradimo pravi ML deo.

    Koristimo postojece isAnomaly oznake iz mock dataset-a kao trenutni detection output.
    Kasnije ovde dolaze metrike iz Isolation Forest evaluacije.
    """
    total = len(df)
    anomaly_count = int(df["isAnomaly"].sum())

    return {
        "currentModel": "Isolation Forest",
        "accuracy": 93.4,
        "precision": 0.91,
        "fpr": 0.07,
        "fnr": 0.05,
        "source": f"Mock dataset - {total} measurements - {anomaly_count} anomalies",
        "comparison": [
            {
                "model": "Isolation Forest",
                "score": 93.4,
            },
            {
                "model": "LOF",
                "score": 87.9,
            },
        ],
    }