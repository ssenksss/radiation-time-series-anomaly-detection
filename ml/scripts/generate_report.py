from pathlib import Path
from datetime import datetime

import pandas as pd

from db import fetch_one, fetch_all


ML_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ML_DIR / "outputs"
REPORT_PATH = OUTPUT_DIR / "ml_report.md"


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


def get_dataset_summary(dataset_id: int) -> dict:
    row = fetch_one(
        """
        SELECT
            d.id,
            d.name,
            d.original_filename,
            d.source_type,
            d.uploaded_at,
            d.row_count,
            d.status,
            COUNT(DISTINCT cm.sensor_id) AS sensor_count,
            COUNT(DISTINCT cm.location) AS location_count,
            MIN(cm.timestamp) AS start_time,
            MAX(cm.timestamp) AS end_time,
            AVG(cm.radiation_level) AS avg_radiation,
            MIN(cm.radiation_level) AS min_radiation,
            MAX(cm.radiation_level) AS max_radiation
        FROM datasets d
        LEFT JOIN clean_measurements cm
            ON d.id = cm.dataset_id
        WHERE d.id = %s
        GROUP BY d.id;
        """,
        (dataset_id,),
    )

    if not row:
        raise RuntimeError(f"Dataset with ID {dataset_id} was not found.")

    return dict(row)


def count_rows(table_name: str, dataset_id: int) -> int:
    row = fetch_one(
        f"""
        SELECT COUNT(*) AS total
        FROM {table_name}
        WHERE dataset_id = %s;
        """,
        (dataset_id,),
    )

    return int(row["total"] or 0)


def get_pipeline_counts(dataset_id: int) -> dict:
    print("Counting raw_measurements...")
    raw_count = count_rows("raw_measurements", dataset_id)

    print("Counting clean_measurements...")
    clean_count = count_rows("clean_measurements", dataset_id)

    print("Counting feature_measurements...")
    feature_count = count_rows("feature_measurements", dataset_id)

    print("Counting anomaly_results...")
    anomaly_result_count = count_rows("anomaly_results", dataset_id)

    return {
        "raw_count": raw_count,
        "clean_count": clean_count,
        "feature_count": feature_count,
        "anomaly_result_count": anomaly_result_count,
    }
def get_label_summary(dataset_id: int) -> dict:
    row = fetch_one(
        """
        SELECT
            COUNT(*) AS total_clean_rows,
            COUNT(original_label) AS labeled_rows,
            COALESCE(SUM(CASE WHEN original_label = TRUE THEN 1 ELSE 0 END), 0) AS true_anomalies,
            COALESCE(SUM(CASE WHEN original_label = FALSE THEN 1 ELSE 0 END), 0) AS normal_rows
        FROM clean_measurements
        WHERE dataset_id = %s;
        """,
        (dataset_id,),
    )

    return {
        "total_clean_rows": int(row["total_clean_rows"] or 0),
        "labeled_rows": int(row["labeled_rows"] or 0),
        "true_anomalies": int(row["true_anomalies"] or 0),
        "normal_rows": int(row["normal_rows"] or 0),
    }


def get_missing_values_summary(dataset_id: int) -> pd.DataFrame:
    rows = fetch_all(
        """
        SELECT
            radiation_level,
            temperature,
            humidity,
            original_label,
            anomaly_type
        FROM clean_measurements
        WHERE dataset_id = %s;
        """,
        (dataset_id,),
    )

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        return pd.DataFrame(columns=["column", "missing_values"])

    missing = dataframe.isna().sum().reset_index()
    missing.columns = ["column", "missing_values"]

    return missing


def get_model_metrics(dataset_id: int) -> pd.DataFrame:
    rows = fetch_all(
        """
        SELECT
            model_name,
            accuracy,
            precision_score,
            recall_score,
            fpr,
            fnr,
            total_records,
            total_anomalies,
            created_at
        FROM model_metrics
        WHERE dataset_id = %s
        ORDER BY model_name;
        """,
        (dataset_id,),
    )

    return pd.DataFrame(rows)


def get_feature_dataframe(dataset_id: int) -> pd.DataFrame:
    rows = fetch_all(
        """
        SELECT
            radiation_level,
            temperature,
            humidity,
            hour_of_day,
            day_of_week,
            rolling_mean,
            rolling_std,
            radiation_diff
        FROM feature_measurements
        WHERE dataset_id = %s
        ORDER BY timestamp;
        """,
        (dataset_id,),
    )

    return pd.DataFrame(rows)


def format_number(value, decimals: int = 4) -> str:
    if value is None or pd.isna(value):
        return "N/A"

    if isinstance(value, float):
        return f"{value:.{decimals}f}"

    return str(value)


def dataframe_to_markdown(dataframe: pd.DataFrame) -> str:
    if dataframe.empty:
        return "_No data available._"

    df = dataframe.copy()

    for column in df.columns:
        df[column] = df[column].apply(
            lambda value: format_number(value) if isinstance(value, float) else str(value)
        )

    headers = list(df.columns)
    lines = []

    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[column]) for column in headers) + " |")

    return "\n".join(lines)


def build_correlation_table(feature_dataframe: pd.DataFrame) -> str:
    if feature_dataframe.empty:
        return "_No feature data available for correlation analysis._"

    numeric_dataframe = feature_dataframe.copy()

    for column in FEATURE_COLUMNS:
        numeric_dataframe[column] = pd.to_numeric(numeric_dataframe[column], errors="coerce")

    correlation = numeric_dataframe[FEATURE_COLUMNS].corr().round(3)

    return dataframe_to_markdown(correlation.reset_index().rename(columns={"index": "feature"}))


def build_report() -> str:
    dataset_id = get_active_dataset_id()

    dataset = get_dataset_summary(dataset_id)
    counts = get_pipeline_counts(dataset_id)
    labels = get_label_summary(dataset_id)
    missing_values = get_missing_values_summary(dataset_id)
    metrics = get_model_metrics(dataset_id)
    feature_dataframe = get_feature_dataframe(dataset_id)

    removed_rows = counts["raw_count"] - counts["clean_count"]

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Radiation Monitoring ML Report",
        "",
        f"Generated at: **{generated_at}**",
        "",
        "## 1. Dataset Summary",
        "",
        f"- Dataset ID: **{dataset['id']}**",
        f"- Dataset name: **{dataset['name']}**",
        f"- Original file: **{dataset['original_filename']}**",
        f"- Source type: **{dataset['source_type']}**",
        f"- Current status: **{dataset['status']}**",
        f"- Uploaded at: **{dataset['uploaded_at']}**",
        f"- Time range: **{dataset['start_time']} → {dataset['end_time']}**",
        f"- Number of sensors: **{dataset['sensor_count']}**",
        f"- Number of locations: **{dataset['location_count']}**",
        f"- Average radiation level: **{format_number(dataset['avg_radiation'])} μSv/h**",
        f"- Minimum radiation level: **{format_number(dataset['min_radiation'])} μSv/h**",
        f"- Maximum radiation level: **{format_number(dataset['max_radiation'])} μSv/h**",
        "",
        "## 2. ELT Pipeline Summary",
        "",
        "The project follows an ELT pipeline. External CSV or ZIP files are first loaded into the raw layer, then cleaned, transformed, enriched with features and used for machine learning analysis.",
        "",
        "| Layer | Table | Row count | Purpose |",
        "|---|---:|---:|---|",
        f"| Raw layer | raw_measurements | {counts['raw_count']} | Stores original extracted values from external CSV files. |",
        f"| Clean layer | clean_measurements | {counts['clean_count']} | Stores cleaned and standardized radiation measurements. |",
        f"| Feature layer | feature_measurements | {counts['feature_count']} | Stores engineered features for ML models. |",
        f"| ML results layer | anomaly_results | {counts['anomaly_result_count']} | Stores anomaly predictions and anomaly scores. |",
        "",
        "## 3. Data Cleaning Summary",
        "",
        f"- Rows loaded into raw layer: **{counts['raw_count']}**",
        f"- Rows kept after cleaning: **{counts['clean_count']}**",
        f"- Rows removed during cleaning: **{removed_rows}**",
        "- Invalid timestamps and invalid radiation values are removed.",
        "- Temperature and humidity missing values are filled with safe median values.",
        "- Empty sensor IDs are replaced with `UNKNOWN_SENSOR`.",
        "- Empty locations are replaced with `Unknown`.",
        "- Original anomaly labels are normalized when they exist in the dataset.",
        "",
        "### Missing Values After Cleaning",
        "",
        dataframe_to_markdown(missing_values),
        "",
        "## 4. Feature Engineering",
        "",
        "The following features are created from cleaned measurements:",
        "",
        "| Feature | Description |",
        "|---|---|",
        "| radiation_level | Cleaned radiation measurement value. |",
        "| temperature | Cleaned temperature value. |",
        "| humidity | Cleaned humidity value. |",
        "| hour_of_day | Hour extracted from timestamp. |",
        "| day_of_week | Day of week extracted from timestamp. |",
        "| rolling_mean | Rolling average of radiation level per sensor. |",
        "| rolling_std | Rolling standard deviation of radiation level per sensor. |",
        "| radiation_diff | Difference from the previous radiation value per sensor. |",
        "",
        "## 5. Label Availability",
        "",
        f"- Clean rows: **{labels['total_clean_rows']}**",
        f"- Rows with original labels: **{labels['labeled_rows']}**",
        f"- Original anomalies: **{labels['true_anomalies']}**",
        f"- Original normal rows: **{labels['normal_rows']}**",
        "",
        "If original labels are available, the project can calculate supervised evaluation metrics such as accuracy, precision, recall, FPR and FNR. If real radiation data does not contain labels, the system works in unsupervised anomaly detection mode.",
        "",
        "## 6. Model Evaluation",
        "",
    ]

    if metrics.empty:
        lines.extend(
            [
                "_No model metrics found. Run the ML pipeline and model evaluation first._",
                "",
            ]
        )
    else:
        metrics_for_report = metrics[
            [
                "model_name",
                "accuracy",
                "precision_score",
                "recall_score",
                "fpr",
                "fnr",
                "total_records",
                "total_anomalies",
            ]
        ]

        lines.extend(
            [
                dataframe_to_markdown(metrics_for_report),
                "",
            ]
        )

    lines.extend(
        [
            "## 7. Correlation and Dimensionality Reduction Note",
            "",
            "A correlation analysis was used to inspect relationships between engineered features. Since the feature set is intentionally small and each feature has a clear time-series interpretation, PCA was not applied in the final prototype.",
            "",
            "### Feature Correlation Matrix",
            "",
            build_correlation_table(feature_dataframe),
            "",
            "## 8. Conclusion",
            "",
            "The project demonstrates a complete analytical pipeline for radiation monitoring: external data ingestion, raw data storage, cleaning, feature engineering, machine learning anomaly detection, model evaluation and dashboard visualization.",
            "",
            "This structure satisfies the requirements for an analytical / ELT-based project and supports the data science part through anomaly detection models and evaluation metrics.",
            "",
        ]
    )

    return "\n".join(lines)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = build_report()

    REPORT_PATH.write_text(report, encoding="utf-8")

    print("ML report generated successfully.")
    print(f"Report path: {REPORT_PATH}")


if __name__ == "__main__":
    main()