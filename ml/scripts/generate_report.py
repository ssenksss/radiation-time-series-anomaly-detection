from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional
import os


import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_recall_curve,
    roc_curve,
)
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier

from db import fetch_one, fetch_all


ML_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ML_DIR / "outputs"
REPORTS_DIR = OUTPUT_DIR / "reports"
TABLES_DIR = OUTPUT_DIR / "tables"
FIGURES_DIR = OUTPUT_DIR / "figures"
REPORT_PATH = REPORTS_DIR / "model_evaluation_report.md"
METRICS_CSV_PATH = TABLES_DIR / "model_metrics_full.csv"
BEST_MARKED_CSV_PATH = TABLES_DIR / "model_metrics_best_marked.csv"

TRAIN_RATIO = 0.70

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

SUPERVISED_MODEL_BUILDERS = {
    "Logistic Regression": {
        "requires_scaling": True,
        "builder": lambda: LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42,
        ),
    },
    "Decision Tree": {
        "requires_scaling": False,
        "builder": lambda: DecisionTreeClassifier(
            max_depth=5,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
        ),
    },
    "Random Forest": {
        "requires_scaling": False,
        "builder": lambda: RandomForestClassifier(
            n_estimators=150,
            max_depth=7,
            min_samples_leaf=4,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
    },
    "Gradient Boosting": {
        "requires_scaling": False,
        "builder": lambda: GradientBoostingClassifier(
            n_estimators=80,
            learning_rate=0.04,
            max_depth=2,
            random_state=42,
        ),
    },
    "KNN Classifier": {
        "requires_scaling": True,
        "builder": lambda: KNeighborsClassifier(
            n_neighbors=9,
            weights="distance",
        ),
    },
}

HIGHER_IS_BETTER = [
    "accuracy",
    "precision_score",
    "recall_score",
    "f1_score",
    "roc_auc",
    "pr_auc",
]

LOWER_IS_BETTER = [
    "fpr",
    "fnr",
    "score_std",
    "score_variance",
    "training_time_seconds",
    "prediction_time_seconds",
]

METRIC_LABELS = {
    "accuracy": "Accuracy",
    "precision_score": "Precision",
    "recall_score": "Recall",
    "f1_score": "F1-score",
    "roc_auc": "ROC-AUC",
    "pr_auc": "PR-AUC",
    "fpr": "FPR",
    "fnr": "FNR",
    "score_mean": "Score mean",
    "score_std": "Score std",
    "score_variance": "Score variance",
}

METRIC_COLUMNS = [
    "model_name",
    "evaluation_mode",
    "accuracy",
    "precision_score",
    "recall_score",
    "f1_score",
    "roc_auc",
    "pr_auc",
    "fpr",
    "fnr",
    "tp",
    "tn",
    "fp",
    "fn",
    "true_anomalies",
    "total_records",
    "total_anomalies",
    "anomaly_rate",
    "score_mean",
    "score_std",
    "score_variance",
    "training_time_seconds",
    "prediction_time_seconds",
    "created_at",
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
    return {
        "raw_count": count_rows("raw_measurements", dataset_id),
        "clean_count": count_rows("clean_measurements", dataset_id),
        "feature_count": count_rows("feature_measurements", dataset_id),
        "anomaly_result_count": count_rows("anomaly_results", dataset_id),
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
            evaluation_mode,
            accuracy,
            precision_score,
            recall_score,
            f1_score,
            roc_auc,
            pr_auc,
            fpr,
            fnr,
            tp,
            tn,
            fp,
            fn,
            true_anomalies,
            total_records,
            total_anomalies,
            CASE
                WHEN total_records > 0 THEN ROUND((total_anomalies::numeric / total_records::numeric) * 100, 3)
                ELSE NULL
            END AS anomaly_rate,
            score_mean,
            score_std,
            score_variance,
            training_time_seconds,
            prediction_time_seconds,
            created_at
        FROM model_metrics
        WHERE dataset_id = %s
        ORDER BY
            CASE evaluation_mode
                WHEN 'labeled' THEN 1
                WHEN 'supervised' THEN 2
                WHEN 'unsupervised' THEN 3
                ELSE 4
            END,
            model_name;
        """,
        (dataset_id,),
    )

    dataframe = pd.DataFrame(rows)

    for column in METRIC_COLUMNS:
        if column not in dataframe.columns:
            dataframe[column] = None

    return dataframe[METRIC_COLUMNS]


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


def get_labeled_feature_dataframe(dataset_id: int) -> pd.DataFrame:
    rows = fetch_all(
        """
        SELECT
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
          AND cm.original_label IS NOT NULL
        ORDER BY fm.timestamp;
        """,
        (dataset_id,),
    )

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        return dataframe

    dataframe["timestamp"] = pd.to_datetime(dataframe["timestamp"])

    for column in FEATURE_COLUMNS:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    dataframe["original_label"] = dataframe["original_label"].astype(int)
    dataframe = dataframe.dropna(subset=["original_label"])

    for column in FEATURE_COLUMNS:
        if dataframe[column].isna().any():
            median_value = dataframe[column].median()
            dataframe[column] = dataframe[column].fillna(0 if pd.isna(median_value) else median_value)

    return dataframe


def chronological_train_test_split(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    split_index = int(len(dataframe) * TRAIN_RATIO)

    if split_index <= 0 or split_index >= len(dataframe):
        return dataframe.copy(), dataframe.copy()

    return dataframe.iloc[:split_index].copy(), dataframe.iloc[split_index:].copy()


def prepare_model_input(
        model_config: dict,
        train_dataframe: pd.DataFrame,
        test_dataframe: pd.DataFrame,
) -> tuple[np.ndarray | pd.DataFrame, np.ndarray | pd.DataFrame]:
    x_train = train_dataframe[FEATURE_COLUMNS]
    x_test = test_dataframe[FEATURE_COLUMNS]

    if model_config.get("requires_scaling"):
        scaler = StandardScaler()
        return scaler.fit_transform(x_train), scaler.transform(x_test)

    return x_train, x_test


def safe_f1_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(f1_score(y_true, y_pred, zero_division=0))


def safe_average_precision(y_true: np.ndarray, y_score: np.ndarray) -> Optional[float]:
    if len(np.unique(y_true)) < 2:
        return None

    return float(average_precision_score(y_true, y_score))


def get_labeled_curve_data(dataset_id: int, model_name: str) -> pd.DataFrame:
    rows = fetch_all(
        """
        SELECT
            ar.timestamp,
            ar.anomaly_score,
            ar.predicted_anomaly,
            cm.original_label
        FROM anomaly_results ar
        JOIN feature_measurements fm
            ON ar.feature_measurement_id = fm.id
        JOIN clean_measurements cm
            ON fm.clean_measurement_id = cm.id
        WHERE ar.dataset_id = %s
          AND ar.model_name = %s
          AND cm.original_label IS NOT NULL
        ORDER BY ar.timestamp;
        """,
        (dataset_id, model_name),
    )

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        return dataframe

    dataframe["timestamp"] = pd.to_datetime(dataframe["timestamp"])

    return keep_test_part(dataframe)


def get_anomaly_scores(dataset_id: int) -> pd.DataFrame:
    rows = fetch_all(
        """
        SELECT
            model_name,
            anomaly_score
        FROM anomaly_results
        WHERE dataset_id = %s
        ORDER BY model_name, timestamp;
        """,
        (dataset_id,),
    )

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        return pd.DataFrame(columns=["model_name", "anomaly_score"])

    dataframe["anomaly_score"] = pd.to_numeric(dataframe["anomaly_score"], errors="coerce")
    dataframe = dataframe.dropna(subset=["anomaly_score"])

    return dataframe


def keep_test_part(dataframe: pd.DataFrame) -> pd.DataFrame:
    split_index = int(len(dataframe) * TRAIN_RATIO)

    if split_index <= 0 or split_index >= len(dataframe):
        return dataframe

    return dataframe.iloc[split_index:].copy()


def format_number(value, decimals: int = 4) -> str:
    if value is None or pd.isna(value):
        return "N/A"

    if isinstance(value, (float, np.floating)):
        return f"{value:.{decimals}f}"

    return str(value)


def dataframe_to_markdown(dataframe: pd.DataFrame) -> str:
    if dataframe.empty:
        return "_No data available._"

    df = dataframe.copy()

    for column in df.columns:
        df[column] = df[column].apply(
            lambda value: format_number(value) if isinstance(value, (float, np.floating)) else str(value)
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


def export_metrics_csv(metrics: pd.DataFrame) -> Optional[Path]:
    if metrics.empty:
        return None

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(METRICS_CSV_PATH, index=False)

    return METRICS_CSV_PATH


def add_best_metric_columns(metrics: pd.DataFrame) -> pd.DataFrame:
    if metrics.empty:
        return metrics.copy()

    result = metrics.copy()
    best_parts = []

    for _, row in result.iterrows():
        markers = []

        for metric in HIGHER_IS_BETTER:
            value = row.get(metric)
            column_values = pd.to_numeric(result[metric], errors="coerce")

            if pd.notna(value) and pd.notna(column_values.max()) and float(value) == float(column_values.max()):
                markers.append(metric)

        for metric in LOWER_IS_BETTER:
            value = row.get(metric)
            column_values = pd.to_numeric(result[metric], errors="coerce")

            if pd.notna(value) and pd.notna(column_values.min()) and float(value) == float(column_values.min()):
                markers.append(metric)

        best_parts.append(", ".join(markers) if markers else "")

    result["best_result_for"] = best_parts

    return result


def export_best_marked_csv(metrics: pd.DataFrame) -> Optional[Path]:
    if metrics.empty:
        return None

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    marked_metrics = add_best_metric_columns(metrics)
    marked_metrics.to_csv(BEST_MARKED_CSV_PATH, index=False)

    return BEST_MARKED_CSV_PATH


def build_best_results_table(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for metric in HIGHER_IS_BETTER:
        rows.append(build_single_best_row(metrics, metric, higher_is_better=True))

    for metric in LOWER_IS_BETTER:
        rows.append(build_single_best_row(metrics, metric, higher_is_better=False))

    rows = [row for row in rows if row is not None]

    return pd.DataFrame(rows)


def get_metric_value(metrics: pd.DataFrame, model_name: str, column: str) -> Optional[float]:
    if metrics.empty or column not in metrics.columns:
        return None

    rows = metrics[metrics["model_name"] == model_name]

    if rows.empty:
        return None

    value = pd.to_numeric(rows.iloc[0].get(column), errors="coerce")

    if pd.isna(value):
        return None

    return float(value)


def format_percent_from_fraction(value: Optional[float], decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "N/A"

    return f"{value * 100:.{decimals}f}%"


def build_interpretation_rows(metrics: pd.DataFrame) -> list[str]:
    if metrics.empty:
        return ["_No model metrics available for interpretation._"]

    kmeans_f1 = get_metric_value(metrics, "K-Means Distance", "f1_score")
    isolation_f1 = get_metric_value(metrics, "Isolation Forest", "f1_score")
    hbos_recall = get_metric_value(metrics, "HBOS", "recall_score")
    hbos_precision = get_metric_value(metrics, "HBOS", "precision_score")
    ocsvm_recall = get_metric_value(metrics, "One-Class SVM", "recall_score")
    ocsvm_precision = get_metric_value(metrics, "One-Class SVM", "precision_score")
    gradient_f1 = get_metric_value(metrics, "Gradient Boosting", "f1_score")
    dbscan_f1 = get_metric_value(metrics, "DBSCAN", "f1_score")
    dbscan_recall = get_metric_value(metrics, "DBSCAN", "recall_score")

    rows = [
        "Accuracy is shown in the table, but I did not use it as the only criterion. The dataset is imbalanced, because normal measurements are much more common than anomalies. For that reason, precision, recall, F1-score, PR-AUC and the confusion matrix are more useful for comparing the models.",
        "",
    ]

    if kmeans_f1 is not None:
        rows.append(
            f"Among the unsupervised models, K-Means Distance had the best balanced result on the labeled test split, with F1-score {kmeans_f1:.3f}. In this run it made the best compromise between finding anomalies and avoiding too many false alarms."
        )

    if isolation_f1 is not None:
        rows.append(
            f"Isolation Forest also gave a stable result, with F1-score {isolation_f1:.3f}. This model is useful for the practical version of the application because it can be trained without manually prepared labels."
        )

    if hbos_recall is not None and hbos_precision is not None:
        rows.append(
            f"HBOS was very sensitive to anomalies, with recall {hbos_recall:.3f}, but its precision was lower ({hbos_precision:.3f}). This means that it detected many true anomalies, but it also produced more false alarms."
        )

    if ocsvm_recall is not None and ocsvm_precision is not None:
        rows.append(
            f"One-Class SVM reached recall {ocsvm_recall:.3f}, while precision was {ocsvm_precision:.3f}. This can be useful when missing an anomaly is a bigger problem than having extra false alarms, but it is not ideal if false alarms need to be low."
        )

    if gradient_f1 is not None and gradient_f1 >= 0.999:
        rows.extend([
            "",
            "### Note on very high supervised results",
            "",
            "Several supervised models achieved very high results on the labeled mock dataset. I do not treat this as proof that the same results would be obtained on real radiation data. The mock dataset has clear anomaly labels and the anomalies are easier to separate than they would usually be in practice.",
            "",
            "For that reason, the supervised part is used as a controlled experiment. It shows that the feature set and the evaluation pipeline work correctly when labels are available. For real datasets without verified labels, the application uses unsupervised detection and does not report accuracy, precision or recall.",
        ])

    rows.extend([
        "",
        "### DBSCAN baseline note",
        "",
        "DBSCAN was kept as a clustering-based baseline, not as the main model for the future real-time version. Standard DBSCAN does not train a reusable classifier with a normal `predict` method for new measurements. It groups the currently loaded points and marks low-density points as noise, so the result depends strongly on the selected dataset and parameters.",
    ])

    if dbscan_f1 is not None and dbscan_recall is not None:
        rows.append(
            f"In this run, DBSCAN achieved F1-score {dbscan_f1:.3f} and recall {dbscan_recall:.3f}. It can detect a part of the anomalous region, but it is less flexible for later real-time use than models that can be trained once and then applied to new records."
        )

    return rows


def build_single_best_row(metrics: pd.DataFrame, metric: str, higher_is_better: bool) -> Optional[dict]:
    if metrics.empty or metric not in metrics.columns:
        return None

    values = pd.to_numeric(metrics[metric], errors="coerce")
    valid_values = values.dropna()

    if valid_values.empty:
        return None

    best_value = valid_values.max() if higher_is_better else valid_values.min()
    tolerance = 1e-9
    best_model_names = metrics.loc[
        values.sub(best_value).abs() <= tolerance,
        "model_name",
    ].tolist()

    return {
        "metric": metric,
        "best_model": ", ".join(best_model_names),
        "value": best_value,
        "criterion": "higher is better" if higher_is_better else "lower is better",
    }


def format_metrics_for_report(metrics: pd.DataFrame) -> pd.DataFrame:
    if metrics.empty:
        return metrics

    report_columns = [
        "model_name",
        "evaluation_mode",
        "accuracy",
        "precision_score",
        "recall_score",
        "f1_score",
        "roc_auc",
        "pr_auc",
        "fpr",
        "fnr",
        "tp",
        "tn",
        "fp",
        "fn",
        "true_anomalies",
        "total_records",
        "total_anomalies",
        "anomaly_rate",
        "score_mean",
        "score_std",
        "score_variance",
        "training_time_seconds",
        "prediction_time_seconds",
        "best_result_for",
    ]

    report_metrics = add_best_metric_columns(metrics)

    return report_metrics[report_columns]


def save_plot(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=160, bbox_inches="tight")
    plt.close()


def plot_metric_bar(metrics: pd.DataFrame, metric: str, title: str, ylabel: str, path: Path) -> Optional[Path]:
    if metrics.empty or metric not in metrics.columns:
        return None

    dataframe = metrics[["model_name", metric]].copy()
    dataframe[metric] = pd.to_numeric(dataframe[metric], errors="coerce")
    dataframe = dataframe.dropna(subset=[metric])

    if dataframe.empty:
        return None

    plt.figure(figsize=(12, 6))
    plt.bar(dataframe["model_name"], dataframe[metric])
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=35, ha="right")
    plt.grid(axis="y", alpha=0.25)
    save_plot(path)

    return path


def prepare_percent_value(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")

    if numeric.dropna().empty:
        return numeric

    if numeric.max() <= 1:
        return numeric * 100

    return numeric


def plot_multi_metric_bar(
        metrics: pd.DataFrame,
        metric_names: list[str],
        title: str,
        path: Path,
        as_percent: bool = False,
) -> Optional[Path]:
    if metrics.empty:
        return None

    dataframe = metrics[["model_name"] + metric_names].copy()

    for metric in metric_names:
        if as_percent:
            dataframe[metric] = prepare_percent_value(dataframe[metric])
        else:
            dataframe[metric] = pd.to_numeric(dataframe[metric], errors="coerce")

    dataframe = dataframe.dropna(subset=metric_names, how="all")

    if dataframe.empty:
        return None

    x = np.arange(len(dataframe))
    width = 0.8 / len(metric_names)

    plt.figure(figsize=(14, 6))

    for index, metric in enumerate(metric_names):
        offset = (index - (len(metric_names) - 1) / 2) * width
        label = METRIC_LABELS.get(metric, metric)
        plt.bar(x + offset, dataframe[metric], width=width, label=label)

    plt.title(title)
    plt.ylabel("score (%)" if as_percent else "score")
    plt.xticks(x, dataframe["model_name"], rotation=35, ha="right")
    plt.legend()
    plt.grid(axis="y", alpha=0.25)

    if as_percent:
        plt.ylim(0, 105)

    save_plot(path)

    return path


def plot_confusion_matrix_group(dataframe: pd.DataFrame, path: Path, title: str) -> Optional[Path]:
    if dataframe.empty:
        return None

    model_count = len(dataframe)
    columns_count = 3 if model_count > 2 else model_count
    rows_count = int(np.ceil(model_count / columns_count))

    figure, axes = plt.subplots(
        rows_count,
        columns_count,
        figsize=(columns_count * 4.4, rows_count * 3.6),
        squeeze=False,
    )
    axes = axes.reshape(-1)

    for axis_index, (_, row) in enumerate(dataframe.iterrows()):
        axis = axes[axis_index]
        matrix = np.array([[row["tn"], row["fp"]], [row["fn"], row["tp"]]], dtype=float)
        row_sums = matrix.sum(axis=1, keepdims=True)
        normalized_matrix = np.divide(
            matrix,
            row_sums,
            out=np.zeros_like(matrix),
            where=row_sums != 0,
        )

        image = axis.imshow(normalized_matrix, vmin=0, vmax=1)
        axis.set_title(row["model_name"], fontsize=10)
        axis.set_xticks([0, 1])
        axis.set_yticks([0, 1])
        axis.set_xticklabels(["pred 0", "pred 1"])
        axis.set_yticklabels(["true 0", "true 1"])

        for i in range(2):
            for j in range(2):
                count_value = int(matrix[i, j])
                percent_value = normalized_matrix[i, j] * 100
                axis.text(
                    j,
                    i,
                    f"{count_value}\n({percent_value:.1f}%)",
                    ha="center",
                    va="center",
                    fontsize=9,
                )

        figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)

    for empty_axis in axes[model_count:]:
        empty_axis.axis("off")

    figure.suptitle(title, y=1.02)
    figure.tight_layout()
    save_plot(path)

    return path


def plot_confusion_matrices(metrics: pd.DataFrame) -> list[Path]:
    columns = ["model_name", "evaluation_mode", "tp", "tn", "fp", "fn"]

    if metrics.empty or not set(columns).issubset(metrics.columns):
        return []

    dataframe = metrics[columns].copy()

    for column in ["tp", "tn", "fp", "fn"]:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    dataframe = dataframe.dropna(subset=["tp", "tn", "fp", "fn"])

    if dataframe.empty:
        return []

    supervised_dataframe = dataframe[dataframe["evaluation_mode"] == "supervised"].copy()
    unsupervised_dataframe = dataframe[dataframe["evaluation_mode"] != "supervised"].copy()

    paths = []

    supervised_path = plot_confusion_matrix_group(
        supervised_dataframe,
        FIGURES_DIR / "confusion_matrices_supervised.png",
        "Confusion matrices for supervised models",
    )
    unsupervised_path = plot_confusion_matrix_group(
        unsupervised_dataframe,
        FIGURES_DIR / "confusion_matrices_unsupervised.png",
        "Confusion matrices for unsupervised anomaly detection models",
    )

    for path in [supervised_path, unsupervised_path]:
        if path is not None:
            paths.append(path)

    return paths


def plot_roc_and_pr_curves(dataset_id: int, metrics: pd.DataFrame) -> tuple[Optional[Path], Optional[Path]]:
    if metrics.empty:
        return None, None

    labeled_models = metrics[metrics["evaluation_mode"].isin(["labeled", "supervised"])]

    if labeled_models.empty:
        return None, None

    roc_path = FIGURES_DIR / "roc_curves.png"
    pr_path = FIGURES_DIR / "precision_recall_curves.png"

    has_roc = False
    has_pr = False

    plt.figure(figsize=(12, 7))

    for _, row in labeled_models.iterrows():
        curve_data = get_labeled_curve_data(dataset_id, row["model_name"])

        if curve_data.empty or curve_data["original_label"].nunique() < 2:
            continue

        y_true = curve_data["original_label"].astype(int).to_numpy()
        y_score = pd.to_numeric(curve_data["anomaly_score"], errors="coerce").to_numpy()
        valid_mask = ~np.isnan(y_score)

        y_true = y_true[valid_mask]
        y_score = y_score[valid_mask]

        if len(y_true) == 0 or len(np.unique(y_true)) < 2:
            continue

        fpr, tpr, _ = roc_curve(y_true, y_score)
        plt.plot(fpr, tpr, label=f"{row['model_name']} ({format_number(row.get('roc_auc'), 3)})")
        has_roc = True

    plt.plot([0, 1], [0, 1], linestyle="--", linewidth=1, label="baseline")
    plt.title("ROC curves on chronological test split")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.legend(fontsize=8, loc="center left", bbox_to_anchor=(1.02, 0.5))
    plt.grid(alpha=0.25)

    if has_roc:
        save_plot(roc_path)
    else:
        plt.close()
        roc_path = None

    plt.figure(figsize=(12, 7))

    for _, row in labeled_models.iterrows():
        curve_data = get_labeled_curve_data(dataset_id, row["model_name"])

        if curve_data.empty or curve_data["original_label"].nunique() < 2:
            continue

        y_true = curve_data["original_label"].astype(int).to_numpy()
        y_score = pd.to_numeric(curve_data["anomaly_score"], errors="coerce").to_numpy()
        valid_mask = ~np.isnan(y_score)

        y_true = y_true[valid_mask]
        y_score = y_score[valid_mask]

        if len(y_true) == 0 or len(np.unique(y_true)) < 2:
            continue

        precision, recall, _ = precision_recall_curve(y_true, y_score)
        plt.plot(recall, precision, label=f"{row['model_name']} ({format_number(row.get('pr_auc'), 3)})")
        has_pr = True

    plt.title("Precision-Recall curves on chronological test split")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.legend(fontsize=8, loc="center left", bbox_to_anchor=(1.02, 0.5))
    plt.grid(alpha=0.25)

    if has_pr:
        save_plot(pr_path)
    else:
        plt.close()
        pr_path = None

    return roc_path, pr_path


def plot_anomaly_score_boxplot(dataset_id: int, path: Path) -> Optional[Path]:
    scores = get_anomaly_scores(dataset_id)

    if scores.empty:
        return None

    model_names = list(scores["model_name"].dropna().unique())
    data = []
    labels = []

    for model_name in model_names:
        values = scores.loc[scores["model_name"] == model_name, "anomaly_score"].dropna().astype(float)

        if values.empty:
            continue

        min_value = values.min()
        max_value = values.max()

        if max_value == min_value:
            normalized_values = values * 0
        else:
            normalized_values = (values - min_value) / (max_value - min_value)

        data.append(normalized_values.to_numpy())
        labels.append(model_name)

    if not data:
        return None

    plt.figure(figsize=(13, 6))
    try:
        plt.boxplot(data, tick_labels=labels, showfliers=False)
    except TypeError:
        plt.boxplot(data, labels=labels, showfliers=False)
    plt.title("Normalized anomaly score distribution by model")
    plt.ylabel("normalized anomaly score")
    plt.xticks(rotation=35, ha="right")
    plt.grid(axis="y", alpha=0.25)
    save_plot(path)

    return path


def plot_anomaly_score_swarm(dataset_id: int, path: Path) -> Optional[Path]:
    scores = get_anomaly_scores(dataset_id)

    if scores.empty:
        return None

    model_names = list(scores["model_name"].dropna().unique())

    if not model_names:
        return None

    plt.figure(figsize=(13, 6))
    rng = np.random.default_rng(42)

    for index, model_name in enumerate(model_names, start=1):
        values = scores.loc[scores["model_name"] == model_name, "anomaly_score"].dropna().astype(float)

        if values.empty:
            continue

        if len(values) > 250:
            values = values.sample(n=250, random_state=42)

        min_value = values.min()
        max_value = values.max()

        if max_value == min_value:
            normalized_values = values * 0
        else:
            normalized_values = (values - min_value) / (max_value - min_value)

        x_values = rng.normal(index, 0.035, size=len(normalized_values))
        plt.scatter(x_values, normalized_values, s=7, alpha=0.28)

    plt.title("Sampled normalized anomaly scores by model")
    plt.ylabel("normalized anomaly score")
    plt.xticks(range(1, len(model_names) + 1), model_names, rotation=35, ha="right")
    plt.grid(axis="y", alpha=0.25)
    save_plot(path)

    return path


def plot_supervised_learning_curves(dataset_id: int, path: Path) -> Optional[Path]:
    dataframe = get_labeled_feature_dataframe(dataset_id)

    if dataframe.empty or dataframe["original_label"].nunique() < 2:
        return None

    train_dataframe, test_dataframe = chronological_train_test_split(dataframe)

    if train_dataframe.empty or test_dataframe.empty or test_dataframe["original_label"].nunique() < 2:
        return None

    train_fractions = [0.20, 0.35, 0.50, 0.65, 0.80, 1.00]
    has_curve = False

    plt.figure(figsize=(12, 7))

    for model_name, model_config in SUPERVISED_MODEL_BUILDERS.items():
        x_points = []
        y_points = []

        for fraction in train_fractions:
            subset_size = max(10, int(len(train_dataframe) * fraction))
            subset = train_dataframe.iloc[:subset_size].copy()

            if subset["original_label"].nunique() < 2:
                continue

            x_train, x_test = prepare_model_input(model_config, subset, test_dataframe)
            y_train = subset["original_label"].astype(int).to_numpy()
            y_test = test_dataframe["original_label"].astype(int).to_numpy()

            model = model_config["builder"]()
            model.fit(x_train, y_train)
            predictions = model.predict(x_test).astype(int)

            x_points.append(subset_size)
            y_points.append(safe_f1_score(y_test, predictions))

        if x_points and y_points:
            plt.plot(x_points, y_points, marker="o", label=model_name)
            has_curve = True

    if not has_curve:
        plt.close()
        return None

    plt.title("F1-score by training set size for supervised models")
    plt.xlabel("training examples")
    plt.ylabel("F1-score")
    plt.ylim(0, 1.05)
    plt.legend(fontsize=8, loc="lower right")
    plt.grid(alpha=0.25)
    save_plot(path)

    return path


def plot_gradient_boosting_staged_performance(dataset_id: int, path: Path) -> Optional[Path]:
    dataframe = get_labeled_feature_dataframe(dataset_id)

    if dataframe.empty or dataframe["original_label"].nunique() < 2:
        return None

    train_dataframe, test_dataframe = chronological_train_test_split(dataframe)

    if train_dataframe.empty or test_dataframe.empty or test_dataframe["original_label"].nunique() < 2:
        return None

    model_config = SUPERVISED_MODEL_BUILDERS["Gradient Boosting"]
    x_train, x_test = prepare_model_input(model_config, train_dataframe, test_dataframe)
    y_train = train_dataframe["original_label"].astype(int).to_numpy()
    y_test = test_dataframe["original_label"].astype(int).to_numpy()

    if len(np.unique(y_train)) < 2 or len(np.unique(y_test)) < 2:
        return None

    model = model_config["builder"]()
    model.fit(x_train, y_train)

    f1_values = []
    pr_auc_values = []
    stages = []

    for stage_index, (predictions, probabilities) in enumerate(
            zip(model.staged_predict(x_test), model.staged_predict_proba(x_test)),
            start=1,
    ):
        if stage_index == 1 or stage_index % 5 == 0 or stage_index == model.n_estimators:
            predictions = np.asarray(predictions).astype(int)
            scores = np.asarray(probabilities)[:, 1]
            stages.append(stage_index)
            f1_values.append(safe_f1_score(y_test, predictions))
            pr_auc_values.append(safe_average_precision(y_test, scores))

    if not stages:
        return None

    plt.figure(figsize=(12, 6))
    plt.plot(stages, f1_values, marker="o", label="F1-score")

    valid_pr_points = [
        (stage, value)
        for stage, value in zip(stages, pr_auc_values)
        if value is not None
    ]

    if valid_pr_points:
        pr_stages, pr_values = zip(*valid_pr_points)
        plt.plot(pr_stages, pr_values, marker="o", label="PR-AUC")

    plt.title("Gradient Boosting staged performance on test split")
    plt.xlabel("number of boosting stages")
    plt.ylabel("score")
    plt.ylim(0, 1.05)
    plt.legend()
    plt.grid(alpha=0.25)
    save_plot(path)

    return path



def remove_obsolete_figures() -> None:
    obsolete_names = [
        "confusion_matrices.png",
        "gradient_boosting_convergence_curve.png",
    ]

    for figure_name in obsolete_names:
        figure_path = FIGURES_DIR / figure_name
        if figure_path.exists():
            figure_path.unlink()

def generate_figures(dataset_id: int, metrics: pd.DataFrame) -> list[Path]:
    remove_obsolete_figures()

    generated_paths = []

    figure_paths = [
        plot_multi_metric_bar(
            metrics,
            ["accuracy", "precision_score", "recall_score", "f1_score"],
            "Model comparison: Accuracy, Precision, Recall and F1-score (%)",
            FIGURES_DIR / "classification_metrics_bar.png",
            as_percent=True,
        ),
        plot_multi_metric_bar(
            metrics,
            ["roc_auc", "pr_auc"],
            "Model comparison: ROC-AUC and PR-AUC",
            FIGURES_DIR / "auc_metrics_bar.png",
        ),
        plot_metric_bar(
            metrics,
            "training_time_seconds",
            "Training time by model",
            "seconds",
            FIGURES_DIR / "training_time_bar.png",
        ),
        plot_metric_bar(
            metrics,
            "prediction_time_seconds",
            "Prediction time by model",
            "seconds",
            FIGURES_DIR / "prediction_time_bar.png",
        ),
        plot_anomaly_score_boxplot(dataset_id, FIGURES_DIR / "anomaly_score_boxplot.png"),
        plot_anomaly_score_swarm(dataset_id, FIGURES_DIR / "anomaly_score_swarm_plot.png"),
        plot_supervised_learning_curves(dataset_id, FIGURES_DIR / "supervised_learning_curves.png"),
        plot_gradient_boosting_staged_performance(dataset_id, FIGURES_DIR / "gradient_boosting_staged_performance.png"),
    ]

    confusion_paths = plot_confusion_matrices(metrics)
    figure_paths.extend(confusion_paths)

    roc_path, pr_path = plot_roc_and_pr_curves(dataset_id, metrics)
    figure_paths.extend([roc_path, pr_path])

    for path in figure_paths:
        if path is not None:
            generated_paths.append(path)

    return generated_paths


def relative_output_path(path: Path) -> str:
    # The report is stored in ml/outputs/reports, so links must be relative to that folder.
    return Path(os.path.relpath(path, start=REPORTS_DIR)).as_posix()


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

    csv_path = export_metrics_csv(metrics)
    best_marked_csv_path = export_best_marked_csv(metrics)
    figure_paths = generate_figures(dataset_id, metrics)
    best_results = build_best_results_table(metrics)
    metrics_for_report = format_metrics_for_report(metrics)

    lines = [
        "# Model Evaluation Report",
        "",
        f"Generated at: **{generated_at}**",
        "",
        "This report is produced by the project script after the model-evaluation step. It summarizes the dataset, used features, trained models, calculated metrics and generated plots.",
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
        "The data pipeline is organized in several steps. The original CSV values are loaded first, then cleaned, transformed into features and finally used for model training, anomaly detection and evaluation.",
        "",
        "| Layer | Table | Row count | Purpose |",
        "|---|---:|---:|---|",
        f"| Raw layer | raw_measurements | {counts['raw_count']} | Stores values loaded from the original CSV file |",
        f"| Clean layer | clean_measurements | {counts['clean_count']} | Stores cleaned radiation measurements |",
        f"| Feature layer | feature_measurements | {counts['feature_count']} | Stores features used by the ML models |",
        f"| ML results layer | anomaly_results | {counts['anomaly_result_count']} | Stores model predictions and anomaly scores |",
        "",
        "## 3. Data Cleaning Summary",
        "",
        f"- Rows loaded into raw layer: **{counts['raw_count']}**",
        f"- Rows kept after cleaning: **{counts['clean_count']}**",
        f"- Rows removed during cleaning: **{removed_rows}**",
        "- Invalid timestamps and invalid radiation values are removed",
        "- Temperature and humidity missing values are filled with median values",
        "- Empty sensor IDs are replaced with `UNKNOWN_SENSOR`",
        "- Empty locations are replaced with `Unknown`",
        "- Original anomaly labels are normalized when they exist in the dataset",
        "",
        "### Missing Values After Cleaning",
        "",
        dataframe_to_markdown(missing_values),
        "",
        "## 4. Feature Engineering",
        "",
        "The models use the following input features:",
        "",
        "| Feature | Description |",
        "|---|---|",
        "| radiation_level | Cleaned radiation measurement value |",
        "| temperature | Cleaned temperature value |",
        "| humidity | Cleaned humidity value |",
        "| hour_of_day | Hour extracted from timestamp |",
        "| day_of_week | Day of week extracted from timestamp |",
        "| rolling_mean | Rolling average of radiation level per sensor |",
        "| rolling_std | Rolling standard deviation of radiation level per sensor |",
        "| radiation_diff | Difference from the previous radiation value per sensor |",
        "",
        "## 5. Label Availability",
        "",
        f"- Clean rows: **{labels['total_clean_rows']}**",
        f"- Rows with original labels: **{labels['labeled_rows']}**",
        f"- Original anomalies: **{labels['true_anomalies']}**",
        f"- Original normal rows: **{labels['normal_rows']}**",
        "",
        "When labels are available, the models are evaluated on the chronological test split. When labels are missing, the system still detects anomalies, but it reports anomaly count, anomaly rate and score statistics instead of classification metrics.",
        "",
        "## 6. Model Selection Rationale",
        "",
        "The selected models cover the two cases that the application needs to support. Some datasets have an `is_anomaly` column, while real measurement files may not have manually checked labels.",
        "",
        "For that reason, both unsupervised and supervised models are kept. Unsupervised models are needed for real unlabeled measurements. Supervised models are used as a controlled comparison when labels exist, because their predictions can be checked against known anomaly labels.",
        "",
        "| Group | Models | Reason for inclusion |",
        "|---|---|---|",
        "| Unsupervised anomaly detection | Isolation Forest, Local Outlier Factor, One-Class SVM, DBSCAN, K-Means Distance, Gaussian Mixture Model, PCA Reconstruction Error, HBOS, ECOD | Used when anomaly labels are not available |",
        "| Supervised classification | Logistic Regression, Decision Tree, Random Forest, Gradient Boosting, KNN Classifier | Used when labels exist and the model can be evaluated directly |",
        "",
        "## 7. Evaluation Methodology",
        "",
        "The dataset is split chronologically: the first 70% of records are used for training and the last 30% for testing. This is more suitable for time-series data than a random split, because random splitting would mix earlier and later measurements and could give an unrealistically clean evaluation.",
        "",
        "When original labels are available, the model predictions are compared with the `is_anomaly` values. The report includes accuracy, precision, recall, F1-score, ROC-AUC, PR-AUC, FPR, FNR and confusion-matrix values. Accuracy is shown, but it is not enough on its own because the dataset contains many more normal measurements than anomalies.",
        "",
        "Regression metrics such as MAE, MSE, RMSE and R² are not used as primary metrics in this experiment, because the goal is not to predict the next exact radiation value. The goal is to mark a measurement as normal or anomalous, or to detect unusual points when labels are missing.",
        "",
        "For real datasets without labels, accuracy, precision, recall and F1-score are not calculated, because there is no ground-truth label. In that case, the application reports detected anomalies, anomaly rate and anomaly score statistics.",
        "",
        "## 8. Model Evaluation Metrics",
        "",
    ]

    if metrics.empty:
        lines.extend(["_No model metrics found. Run the ML pipeline and model evaluation first._", ""])
    else:
        lines.extend(
            [
                "The table below contains the stored metrics for all evaluated models. For labeled and supervised evaluation, the values are calculated on the chronological test split.",
                "",
                dataframe_to_markdown(metrics_for_report),
                "",
            ]
        )

        if csv_path:
            lines.extend(
                [
                    f"Full metrics CSV: `{relative_output_path(csv_path)}`",
                    "",
                ]
            )

        if best_marked_csv_path:
            lines.extend(
                [
                    f"Best-marked metrics CSV: `{relative_output_path(best_marked_csv_path)}`",
                    "",
                ]
            )

    lines.extend(
        [
            "## 9. Best Results by Metric",
            "",
            "If more than one model has the same best value for a metric, all of them are listed in the `best_model` column.",
            "",
            dataframe_to_markdown(best_results),
            "",
            "## 10. Result Interpretation",
            "",
            *build_interpretation_rows(metrics),
            "",
            "## 11. Generated Figures",
            "",
            "The figures are used to support the metric table. Confusion matrices show correct and incorrect predictions, ROC and PR curves show model behavior across thresholds, and box/swarm plots show the distribution of anomaly scores. Learning curves are included for supervised models, where the training size can be varied in a standard way.",
            "",
        ]
    )

    if figure_paths:
        for path in figure_paths:
            relative_path = relative_output_path(path)
            figure_title = path.stem.replace("_", " ").title()
            lines.extend([f"### {figure_title}", "", f"![{figure_title}]({relative_path})", ""])
    else:
        lines.extend(["_No figures were generated._", ""])

    lines.extend(
        [
            "## 12. Feature Correlation Matrix",
            "",
            build_correlation_table(feature_dataframe),
            "",
            "## 13. Conclusion",
            "",
            "The evaluation shows that the system can train and compare traditional machine-learning models for radiation anomaly detection. The strongest supervised results were obtained on the labeled mock dataset, where anomaly patterns are clearly defined. These results are useful for checking the pipeline, but they should not be treated as guaranteed performance on real radiation-monitoring data.",
            "",
            "For the practical version of the application, the unsupervised workflow is especially important. It allows the system to work with real datasets that do not contain an `is_anomaly` column. In that case, the model creates the `predicted_anomaly` result, and the application reports anomaly counts and score statistics instead of supervised metrics.",
            "",
            "The comparison table, best-result markers and generated figures can be used later in the thesis discussion and in the Model Testing view of the application.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    report = build_report()
    REPORT_PATH.write_text(report, encoding="utf-8")

    print("ML evaluation outputs generated successfully")
    print(f"Report path: {REPORT_PATH}")
    print(f"Full metrics CSV path: {METRICS_CSV_PATH}")
    print(f"Best-marked CSV path: {BEST_MARKED_CSV_PATH}")
    print(f"Figures directory: {FIGURES_DIR}")


if __name__ == "__main__":
    main()