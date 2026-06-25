from pathlib import Path
from datetime import datetime
from typing import Optional

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

from db import fetch_one, fetch_all


ML_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ML_DIR / "outputs"
REPORT_PATH = OUTPUT_DIR / "train_test_report.md"
CSV_PATH = OUTPUT_DIR / "train_test_metrics.csv"

FEATURE_COLUMNS = [
    "radiation_level",
    "temperature",
    "humidity",
    "hour_of_day",
    "day_of_week",
    "rolling_mean",
    "rolling_std",
    "radiation_diff",
]

TRAIN_RATIO = 0.70
MAX_CONTAMINATION = 0.20
FALLBACK_CONTAMINATION = 0.03


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


def get_dataset_name(dataset_id: int) -> str:
    row = fetch_one(
        """
        SELECT name
        FROM datasets
        WHERE id = %s;
        """,
        (dataset_id,),
    )

    if not row:
        return f"Dataset {dataset_id}"

    return str(row["name"])


def load_feature_dataset(dataset_id: int) -> pd.DataFrame:
    rows = fetch_all(
        """
        SELECT
            fm.id AS feature_measurement_id,
            fm.timestamp,
            fm.radiation_level,
            fm.temperature,
            fm.humidity,
            fm.hour_of_day,
            fm.day_of_week,
            fm.rolling_mean,
            fm.rolling_std,
            fm.radiation_diff,
            cm.original_label
        FROM feature_measurements fm
        JOIN clean_measurements cm
            ON fm.clean_measurement_id = cm.id
        WHERE fm.dataset_id = %s
        ORDER BY fm.timestamp;
        """,
        (dataset_id,),
    )

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        raise RuntimeError("No feature measurements found. Run create_features.py first.")

    dataframe["timestamp"] = pd.to_datetime(dataframe["timestamp"])
    dataframe = dataframe.sort_values("timestamp").reset_index(drop=True)

    for column in FEATURE_COLUMNS:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    medians = dataframe[FEATURE_COLUMNS].median(numeric_only=True)
    dataframe[FEATURE_COLUMNS] = dataframe[FEATURE_COLUMNS].fillna(medians)
    dataframe[FEATURE_COLUMNS] = dataframe[FEATURE_COLUMNS].fillna(0)

    return dataframe


def calculate_contamination(
        train_dataframe: pd.DataFrame,
        threshold: float,
        y_train: Optional[pd.Series],
) -> float:
    if y_train is not None and len(y_train) > 0 and bool(y_train.any()):
        label_ratio = float(y_train.mean())
        if label_ratio > 0:
            return min(MAX_CONTAMINATION, label_ratio)

    ratio_above_threshold = float((train_dataframe["radiation_level"] > threshold).mean())

    if ratio_above_threshold <= 0:
        return 0.0

    return min(MAX_CONTAMINATION, ratio_above_threshold)


def split_chronologically(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if len(dataframe) < 10:
        raise RuntimeError("At least 10 rows are required for train/test evaluation.")

    split_index = int(len(dataframe) * TRAIN_RATIO)

    if split_index <= 0 or split_index >= len(dataframe):
        raise RuntimeError("Unable to create a valid train/test split.")

    train_dataframe = dataframe.iloc[:split_index].copy()
    test_dataframe = dataframe.iloc[split_index:].copy()

    return train_dataframe, test_dataframe


def labels_available(dataframe: pd.DataFrame) -> bool:
    if "original_label" not in dataframe.columns:
        return False

    labeled_rows = dataframe["original_label"].notna().sum()

    if labeled_rows == 0:
        return False

    return bool(dataframe["original_label"].fillna(False).astype(bool).any())


def calculate_metrics(y_true: pd.Series, y_pred: pd.Series) -> dict:
    y_true_bool = y_true.astype(bool)
    y_pred_bool = y_pred.astype(bool)

    accuracy = accuracy_score(y_true_bool, y_pred_bool) * 100
    precision = precision_score(y_true_bool, y_pred_bool, zero_division=0)
    recall = recall_score(y_true_bool, y_pred_bool, zero_division=0)

    tn, fp, fn, tp = confusion_matrix(
        y_true_bool,
        y_pred_bool,
        labels=[False, True],
    ).ravel()

    fpr = fp / (fp + tn) if (fp + tn) else 0
    fnr = fn / (fn + tp) if (fn + tp) else 0

    return {
        "accuracy": round(float(accuracy), 2),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "fpr": round(float(fpr), 4),
        "fnr": round(float(fnr), 4),
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
    }


def train_and_test_isolation_forest(
        train_dataframe: pd.DataFrame,
        test_dataframe: pd.DataFrame,
        threshold: float,
        y_train: Optional[pd.Series],
) -> dict:
    contamination = calculate_contamination(train_dataframe, threshold, y_train)

    if contamination <= 0:
        predictions = pd.Series([False] * len(test_dataframe), index=test_dataframe.index)
        return {
            "model_name": "Isolation Forest",
            "contamination": 0.0,
            "predictions": predictions,
        }

    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(train_dataframe[FEATURE_COLUMNS])
    test_scaled = scaler.transform(test_dataframe[FEATURE_COLUMNS])

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(train_scaled)
    raw_predictions = model.predict(test_scaled)

    predictions = pd.Series(raw_predictions == -1, index=test_dataframe.index)

    return {
        "model_name": "Isolation Forest",
        "contamination": round(float(contamination), 5),
        "predictions": predictions,
    }


def train_and_test_lof(
        train_dataframe: pd.DataFrame,
        test_dataframe: pd.DataFrame,
        threshold: float,
        y_train: Optional[pd.Series],
) -> dict:
    contamination = calculate_contamination(train_dataframe, threshold, y_train)

    if contamination <= 0:
        predictions = pd.Series([False] * len(test_dataframe), index=test_dataframe.index)
        return {
            "model_name": "Local Outlier Factor",
            "contamination": 0.0,
            "predictions": predictions,
        }

    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(train_dataframe[FEATURE_COLUMNS])
    test_scaled = scaler.transform(test_dataframe[FEATURE_COLUMNS])

    n_neighbors = min(35, max(2, len(train_dataframe) - 1))

    model = LocalOutlierFactor(
        n_neighbors=n_neighbors,
        contamination=contamination,
        novelty=True,
        metric="minkowski",
        n_jobs=-1,
    )

    model.fit(train_scaled)
    raw_predictions = model.predict(test_scaled)

    predictions = pd.Series(raw_predictions == -1, index=test_dataframe.index)

    return {
        "model_name": "Local Outlier Factor",
        "contamination": round(float(contamination), 5),
        "n_neighbors": int(n_neighbors),
        "predictions": predictions,
    }


def dataframe_to_markdown(dataframe: pd.DataFrame) -> str:
    if dataframe.empty:
        return "_No data available._"

    headers = list(dataframe.columns)
    lines = []

    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for _, row in dataframe.iterrows():
        lines.append("| " + " | ".join(str(row[column]) for column in headers) + " |")

    return "\n".join(lines)


def build_report(
        dataset_id: int,
        dataset_name: str,
        threshold: float,
        train_dataframe: pd.DataFrame,
        test_dataframe: pd.DataFrame,
        metrics_dataframe: pd.DataFrame,
        has_labels: bool,
) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    train_start = train_dataframe["timestamp"].min()
    train_end = train_dataframe["timestamp"].max()
    test_start = test_dataframe["timestamp"].min()
    test_end = test_dataframe["timestamp"].max()

    lines = [
        "# Train/Test Evaluation Report",
        "",
        f"Generated at: **{generated_at}**",
        "",
        "## 1. Purpose",
        "",
        "This report documents the train/test evaluation step required for the data science part of the project. Since the dataset is a time series, the split is chronological instead of random, which prevents future measurements from leaking into the training set.",
        "",
        "## 2. Dataset and Split",
        "",
        f"- Dataset ID: **{dataset_id}**",
        f"- Dataset name: **{dataset_name}**",
        f"- Threshold used for model sensitivity: **{threshold} μSv/h**",
        f"- Total records used: **{len(train_dataframe) + len(test_dataframe)}**",
        f"- Training set: **{len(train_dataframe)} records** ({int(TRAIN_RATIO * 100)}%)",
        f"- Test set: **{len(test_dataframe)} records** ({100 - int(TRAIN_RATIO * 100)}%)",
        f"- Training time range: **{train_start} → {train_end}**",
        f"- Test time range: **{test_start} → {test_end}**",
        "",
        "## 3. Label Availability",
        "",
    ]

    if has_labels:
        train_anomalies = int(train_dataframe["original_label"].fillna(False).astype(bool).sum())
        test_anomalies = int(test_dataframe["original_label"].fillna(False).astype(bool).sum())

        lines.extend(
            [
                "Original anomaly labels are available, so supervised metrics can be calculated on the test set.",
                "",
                f"- Original anomalies in training set: **{train_anomalies}**",
                f"- Original anomalies in test set: **{test_anomalies}**",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "Original anomaly labels are not available. The train/test split is still documented, but supervised metrics cannot be calculated without ground-truth labels. This is expected for real unlabeled radiation data.",
                "",
            ]
        )

    lines.extend(
        [
            "## 4. Models",
            "",
            "Two anomaly detection models were trained on the training part of the time series and evaluated on the test part:",
            "",
            "- Isolation Forest",
            "- Local Outlier Factor with `novelty=True`, which allows prediction on previously unseen test data",
            "",
            "## 5. Test Metrics",
            "",
            dataframe_to_markdown(metrics_dataframe),
            "",
            "## 6. Conclusion",
            "",
            "This report confirms that the project includes a separate model evaluation step with a chronological train/test split. This complements the main dashboard evaluation and provides academic evidence for the machine learning workflow.",
            "",
        ]
    )

    return "\n".join(lines)


def run_train_test_evaluation() -> pd.DataFrame:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    dataset_id = get_active_dataset_id()
    dataset_name = get_dataset_name(dataset_id)
    threshold = get_threshold()

    dataframe = load_feature_dataset(dataset_id)
    train_dataframe, test_dataframe = split_chronologically(dataframe)

    has_labels = labels_available(dataframe)
    y_train = None
    y_test = None

    if has_labels:
        y_train = train_dataframe["original_label"].fillna(False).astype(bool)
        y_test = test_dataframe["original_label"].fillna(False).astype(bool)

    model_results = [
        train_and_test_isolation_forest(train_dataframe, test_dataframe, threshold, y_train),
        train_and_test_lof(train_dataframe, test_dataframe, threshold, y_train),
    ]

    output_rows = []

    for result in model_results:
        predictions = result["predictions"]
        predicted_anomalies = int(predictions.sum())

        row = {
            "model_name": result["model_name"],
            "evaluation_mode": "supervised_train_test" if has_labels else "unsupervised_train_test",
            "train_records": len(train_dataframe),
            "test_records": len(test_dataframe),
            "contamination": result["contamination"],
            "predicted_test_anomalies": predicted_anomalies,
        }

        if "n_neighbors" in result:
            row["n_neighbors"] = result["n_neighbors"]
        else:
            row["n_neighbors"] = "N/A"

        if has_labels and y_test is not None:
            metrics = calculate_metrics(y_test, predictions)
            row.update(metrics)
        else:
            row.update(
                {
                    "accuracy": "N/A",
                    "precision": "N/A",
                    "recall": "N/A",
                    "fpr": "N/A",
                    "fnr": "N/A",
                    "tp": "N/A",
                    "tn": "N/A",
                    "fp": "N/A",
                    "fn": "N/A",
                }
            )

        output_rows.append(row)

    metrics_dataframe = pd.DataFrame(output_rows)
    metrics_dataframe.to_csv(CSV_PATH, index=False)

    report = build_report(
        dataset_id=dataset_id,
        dataset_name=dataset_name,
        threshold=threshold,
        train_dataframe=train_dataframe,
        test_dataframe=test_dataframe,
        metrics_dataframe=metrics_dataframe,
        has_labels=has_labels,
    )

    REPORT_PATH.write_text(report, encoding="utf-8")

    print("Train/test evaluation completed successfully.")
    print(f"Dataset ID: {dataset_id}")
    print(f"Train records: {len(train_dataframe)}")
    print(f"Test records: {len(test_dataframe)}")
    print(f"Report path: {REPORT_PATH}")
    print(f"CSV path: {CSV_PATH}")

    return metrics_dataframe


def main():
    run_train_test_evaluation()


if __name__ == "__main__":
    main()