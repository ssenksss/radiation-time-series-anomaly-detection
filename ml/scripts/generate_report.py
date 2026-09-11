from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional
import os


import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd
from sklearn.metrics import (
    f1_score,
    log_loss,
    precision_recall_curve,
    roc_curve,
)
from sklearn.preprocessing import StandardScaler

from ml.models.supervised.train_logistic_regression import (
    MODEL_NAME as LOGISTIC_REGRESSION_NAME,
    REQUIRES_SCALING as LOGISTIC_REGRESSION_SCALING,
    build_model as build_logistic_regression,
)
from ml.models.supervised.train_decision_tree import (
    MODEL_NAME as DECISION_TREE_NAME,
    REQUIRES_SCALING as DECISION_TREE_SCALING,
    build_model as build_decision_tree,
)
from ml.models.supervised.train_random_forest import (
    MODEL_NAME as RANDOM_FOREST_NAME,
    REQUIRES_SCALING as RANDOM_FOREST_SCALING,
    build_model as build_random_forest,
)
from ml.models.supervised.train_gradient_boosting import (
    MODEL_NAME as GRADIENT_BOOSTING_NAME,
    REQUIRES_SCALING as GRADIENT_BOOSTING_SCALING,
    build_model as build_gradient_boosting,
)
from ml.models.supervised.train_knn_classifier import (
    MODEL_NAME as KNN_CLASSIFIER_NAME,
    REQUIRES_SCALING as KNN_CLASSIFIER_SCALING,
    build_model as build_knn_classifier,
)

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

SUPERVISED_MODELS = [
    {
        "name": LOGISTIC_REGRESSION_NAME,
        "requires_scaling": LOGISTIC_REGRESSION_SCALING,
        "build_model": build_logistic_regression,
    },
    {
        "name": DECISION_TREE_NAME,
        "requires_scaling": DECISION_TREE_SCALING,
        "build_model": build_decision_tree,
    },
    {
        "name": RANDOM_FOREST_NAME,
        "requires_scaling": RANDOM_FOREST_SCALING,
        "build_model": build_random_forest,
    },
    {
        "name": GRADIENT_BOOSTING_NAME,
        "requires_scaling": GRADIENT_BOOSTING_SCALING,
        "build_model": build_gradient_boosting,
    },
    {
        "name": KNN_CLASSIFIER_NAME,
        "requires_scaling": KNN_CLASSIFIER_SCALING,
        "build_model": build_knn_classifier,
    },
]


MODEL_ORDER = [
    "Isolation Forest",
    "Local Outlier Factor",
    "One-Class SVM",
    "DBSCAN",
    "K-Means",
    "Gaussian Mixture Model",
    "PCA",
    "HBOS",
    "ECOD",
    "Logistic Regression",
    "Decision Tree",
    "Random Forest",
    "Gradient Boosting",
    "KNN Classifier",
]

# pastel model colors used consistently in every figure
MODEL_COLORS = {
    "Isolation Forest": "#6CC9FEDA",
    "Local Outlier Factor": "#FDBF6F",
    "One-Class SVM": "#7BFA7FE1",
    "DBSCAN": "#FB8072",
    "K-Means": "#B39DDB",
    "Gaussian Mixture Model": "#C49A6C",
    "PCA": "#88B3CA",
    "HBOS": "#BDBDBD",
    "ECOD": "#D9D76E",

    "Logistic Regression": "#80CDC1",
    "Decision Tree": "#C4E7FA",
    "Random Forest": "#F082CB",
    "Gradient Boosting": "#C5F79A",
    "KNN Classifier": "#F4A6A6",
}

FEATURE_COLORS = [
    "#7BAFD4",
    "#F4B860",
    "#7ACFA6",
    "#F28B82",
    "#B69DE6",
    "#E6A1C9",
    "#8FD3F4",
    "#7DD3C7",
]

FIGURE_BACKGROUND = "#FAFAFA"
AXES_BACKGROUND = "#FFFFFF"
TEXT_COLOR = "#1F2937"
MUTED_TEXT_COLOR = "#6B7280"
GRID_COLOR = "#E5E7EB"
BORDER_COLOR = "#9CA3AF"
UNSUPERVISED_GROUP_COLOR = "#8CBAD9"
SUPERVISED_GROUP_COLOR = "#F6C78F"

CONFUSION_CMAP = LinearSegmentedColormap.from_list(
    "soft_confusion_blue",
    ["#F8FBFF", "#DBEAFE", "#93C5FD", "#3B82F6", "#1D4ED8"],
)

CORRELATION_CMAP = LinearSegmentedColormap.from_list(
    "soft_correlation",
    ["#6BAED6", "#F7FBFF", "#FB8072"],
)

# clean publication-style plot defaults
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "figure.facecolor": FIGURE_BACKGROUND,
    "axes.facecolor": AXES_BACKGROUND,
    "axes.edgecolor": BORDER_COLOR,
    "axes.labelcolor": TEXT_COLOR,
    "xtick.color": TEXT_COLOR,
    "ytick.color": TEXT_COLOR,
    "text.color": TEXT_COLOR,
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.titleweight": "semibold",
    "axes.labelsize": 11,
    "figure.titlesize": 17,
    "figure.titleweight": "semibold",
    "legend.fontsize": 8.5,
    "grid.color": GRID_COLOR,
    "grid.linewidth": 0.65,
    "grid.alpha": 0.55,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "savefig.dpi": 300,
})


def get_model_color(model_name: str):
    return MODEL_COLORS.get(model_name, "#64748B")


def get_model_group_color(model_name: str) -> str:
    if model_name in MODEL_ORDER[9:]:
        return SUPERVISED_GROUP_COLOR
    return UNSUPERVISED_GROUP_COLOR


def style_axes(axis, grid_axis: str = "y", show_grid: bool = True) -> None:
    axis.set_facecolor(AXES_BACKGROUND)
    axis.spines["left"].set_color(BORDER_COLOR)
    axis.spines["bottom"].set_color(BORDER_COLOR)
    axis.spines["left"].set_linewidth(0.9)
    axis.spines["bottom"].set_linewidth(0.9)
    axis.tick_params(axis="both", labelsize=9.5, length=3.5, width=0.8)

    if show_grid:
        axis.grid(axis=grid_axis, linestyle="--", linewidth=0.65, alpha=0.55)
        axis.set_axisbelow(True)


def style_legend(axis, location: str = "best", columns: int = 1) -> None:
    legend = axis.legend(
        loc=location,
        ncol=columns,
        frameon=True,
        facecolor="white",
        edgecolor="#E5E7EB",
        framealpha=0.96,
        fancybox=True,
    )

    if legend is not None:
        legend.get_frame().set_linewidth(0.8)


def apply_boxplot_style(result, colors: list[str]) -> None:
    for patch, color in zip(result["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.78)
        patch.set_edgecolor("#374151")
        patch.set_linewidth(0.9)

    for median in result["medians"]:
        median.set_color("#111827")
        median.set_linewidth(1.5)

    for whisker in result["whiskers"]:
        whisker.set_color("#6B7280")
        whisker.set_linewidth(0.9)

    for cap in result["caps"]:
        cap.set_color("#6B7280")
        cap.set_linewidth(0.9)


def order_model_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty or "model_name" not in dataframe.columns:
        return dataframe

    order_map = {
        model_name: index
        for index, model_name in enumerate(MODEL_ORDER)
    }

    result = dataframe.copy()
    result["_model_order"] = (
        result["model_name"]
        .map(order_map)
        .fillna(len(MODEL_ORDER))
    )

    return (
        result
        .sort_values(["_model_order", "model_name"])
        .drop(columns=["_model_order"])
        .reset_index(drop=True)
    )


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
    # load metrics saved by the evaluation step
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

    dataframe["timestamp"] = pd.to_datetime(
        dataframe["timestamp"]
    )

    for column in FEATURE_COLUMNS:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

    dataframe["original_label"] = (
        dataframe["original_label"]
        .astype(int)
    )

    dataframe = dataframe.dropna(
        subset=["original_label"]
    )

    return dataframe


def chronological_train_test_split(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    ordered_dataframe = (
        dataframe
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    split_index = int(
        len(ordered_dataframe)
        * TRAIN_RATIO
    )

    if (
        split_index <= 0
        or split_index >= len(ordered_dataframe)
    ):
        return (
            ordered_dataframe.copy(),
            ordered_dataframe.copy(),
        )

    train_dataframe = (
        ordered_dataframe
        .iloc[:split_index]
        .copy()
    )

    test_dataframe = (
        ordered_dataframe
        .iloc[split_index:]
        .copy()
    )

    train_medians = (
        train_dataframe[
            FEATURE_COLUMNS
        ]
        .median(
            numeric_only=True
        )
    )

    train_dataframe[
        FEATURE_COLUMNS
    ] = (
        train_dataframe[
            FEATURE_COLUMNS
        ]
        .fillna(train_medians)
        .fillna(0)
    )

    test_dataframe[
        FEATURE_COLUMNS
    ] = (
        test_dataframe[
            FEATURE_COLUMNS
        ]
        .fillna(train_medians)
        .fillna(0)
    )

    return (
        train_dataframe,
        test_dataframe,
    )


def chronological_train_validation_split(
    train_dataframe: pd.DataFrame,
    validation_ratio: float = 0.20,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    split_index = int(len(train_dataframe) * (1 - validation_ratio))

    if split_index <= 0 or split_index >= len(train_dataframe):
        return train_dataframe.copy(), train_dataframe.copy()

    fit_dataframe = train_dataframe.iloc[:split_index].copy()
    validation_dataframe = train_dataframe.iloc[split_index:].copy()

    fit_medians = fit_dataframe[FEATURE_COLUMNS].median(numeric_only=True)

    fit_dataframe[FEATURE_COLUMNS] = (
        fit_dataframe[FEATURE_COLUMNS]
        .fillna(fit_medians)
        .fillna(0)
    )

    validation_dataframe[FEATURE_COLUMNS] = (
        validation_dataframe[FEATURE_COLUMNS]
        .fillna(fit_medians)
        .fillna(0)
    )

    return fit_dataframe, validation_dataframe


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





def get_labeled_curve_data(
    dataset_id: int,
    model_name: str,
) -> pd.DataFrame:
    rows = fetch_all(
        """
        SELECT
            ar.feature_measurement_id,
            ar.timestamp,
            ar.anomaly_score,
            ar.predicted_anomaly,
            ar.evaluation_split,
            cm.original_label
        FROM anomaly_results ar
        JOIN feature_measurements fm
            ON ar.feature_measurement_id = fm.id
        JOIN clean_measurements cm
            ON fm.clean_measurement_id = cm.id
        WHERE ar.dataset_id = %s
          AND ar.model_name = %s
          AND ar.evaluation_split = 'test'
          AND cm.original_label IS NOT NULL
        ORDER BY ar.timestamp;
        """,
        (
            dataset_id,
            model_name,
        ),
    )

    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        return dataframe

    dataframe["timestamp"] = pd.to_datetime(
        dataframe["timestamp"]
    )

    return dataframe


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
    # mark best values so the comparison table is easier to read
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
    # compare metrics where higher and lower values have different meaning
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

    rows = [
        "Accuracy is shown in the table, but I did not use it as the only criterion. The dataset is imbalanced, because normal measurements are much more common than anomalies. For that reason, precision, recall, F1-score, PR-AUC and the confusion matrix are more useful for comparing the models.",
        "",
        "Precision–Recall curves are interpreted together with the positive-class baseline. When anomalies are rare, the PR curve can look irregular and can drop quickly as recall increases. This is not a plotting error: it shows that a model can detect more anomalies only by accepting more false-positive alarms, which lowers precision.",
        "",
    ]

    unsupervised_model_names = [
        "Isolation Forest",
        "Local Outlier Factor",
        "One-Class SVM",
        "DBSCAN",
        "K-Means",
        "Gaussian Mixture Model",
        "PCA",
        "HBOS",
        "ECOD",
    ]

    unsupervised_metrics = metrics[
        metrics["model_name"].isin(unsupervised_model_names)
    ].copy()

    if not unsupervised_metrics.empty:
        unsupervised_metrics["f1_score"] = pd.to_numeric(
            unsupervised_metrics["f1_score"],
            errors="coerce",
        )

        valid_f1 = unsupervised_metrics.dropna(subset=["f1_score"])

        if not valid_f1.empty:
            best_row = valid_f1.loc[
                valid_f1["f1_score"].idxmax()
            ]

            rows.append(
                f"Among the unsupervised models, {best_row['model_name']} had the highest F1-score on the labeled test split, with F1-score {best_row['f1_score']:.3f}. This indicates the best balance between precision and recall among the currently available unsupervised results."
            )

    isolation_f1 = get_metric_value(
        metrics,
        "Isolation Forest",
        "f1_score",
    )

    isolation_roc = get_metric_value(
        metrics,
        "Isolation Forest",
        "roc_auc",
    )

    isolation_pr = get_metric_value(
        metrics,
        "Isolation Forest",
        "pr_auc",
    )

    if (
        isolation_f1 is not None
        and isolation_roc is not None
        and isolation_pr is not None
    ):
        rows.append(
            f"Isolation Forest achieved F1-score {isolation_f1:.3f}, ROC-AUC {isolation_roc:.3f} and PR-AUC {isolation_pr:.3f}. It is relevant for the practical version of the application because it can be trained without manually prepared anomaly labels."
        )

    hbos_recall = get_metric_value(
        metrics,
        "HBOS",
        "recall_score",
    )

    hbos_precision = get_metric_value(
        metrics,
        "HBOS",
        "precision_score",
    )

    if hbos_recall is not None and hbos_precision is not None:
        rows.append(
            f"HBOS reached recall {hbos_recall:.3f} and precision {hbos_precision:.3f}. A higher recall means that more true anomalies were detected, while lower precision indicates a larger number of false alarms."
        )

    ocsvm_recall = get_metric_value(
        metrics,
        "One-Class SVM",
        "recall_score",
    )

    ocsvm_precision = get_metric_value(
        metrics,
        "One-Class SVM",
        "precision_score",
    )

    if ocsvm_recall is not None and ocsvm_precision is not None:
        rows.append(
            f"One-Class SVM reached recall {ocsvm_recall:.3f} and precision {ocsvm_precision:.3f}. This result shows the trade-off between detecting more anomalies and producing additional false positive predictions."
        )

    rows.extend(
        [
            "",
            "### DBSCAN baseline note",
            "",
            "DBSCAN was kept as a clustering-based baseline, not as the main model for the future real-time version. Standard DBSCAN does not train a reusable classifier with a normal `predict` method for new measurements. It groups the currently loaded points and marks low-density points as noise, so the result depends strongly on the selected dataset and parameters.",
        ]
    )

    dbscan_f1 = get_metric_value(
        metrics,
        "DBSCAN",
        "f1_score",
    )

    dbscan_recall = get_metric_value(
        metrics,
        "DBSCAN",
        "recall_score",
    )

    if dbscan_f1 is not None and dbscan_recall is not None:
        rows.append(
            f"In this run, DBSCAN achieved F1-score {dbscan_f1:.3f} and recall {dbscan_recall:.3f}. It is useful as a clustering baseline, but it is less suitable for direct application to future streaming measurements than models with a standard train-and-predict workflow."
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
    plt.savefig(path, dpi=300, bbox_inches="tight", facecolor=FIGURE_BACKGROUND)
    plt.close()


def clear_figures_directory() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    image_extensions = {".png", ".jpg", ".jpeg", ".svg", ".pdf"}

    for item in FIGURES_DIR.iterdir():
        if item.is_file() and item.suffix.lower() in image_extensions:
            item.unlink()


def add_bar_value_labels(axis, bars, decimals: int = 3, suffix: str = "") -> None:
    for bar in bars:
        value = bar.get_width() if bar.get_width() > 0 else bar.get_height()

        if not np.isfinite(value):
            continue

        if bar.get_width() > bar.get_height():
            axis.text(
                bar.get_width(),
                bar.get_y() + bar.get_height() / 2,
                f"  {value:.{decimals}f}{suffix}",
                va="center",
                ha="left",
                fontsize=9,
            )
        else:
            axis.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{value:.{decimals}f}{suffix}",
                va="bottom",
                ha="center",
                fontsize=8,
            )


def plot_metric_bar(
    metrics: pd.DataFrame,
    metric: str,
    title: str,
    ylabel: str,
    path: Path,
) -> Optional[Path]:
    if metrics.empty or metric not in metrics.columns:
        return None

    dataframe = metrics[["model_name", metric]].copy()
    dataframe[metric] = pd.to_numeric(dataframe[metric], errors="coerce")
    dataframe = dataframe.dropna(subset=[metric])

    if dataframe.empty:
        return None

    # timing charts are ordered from fastest to slowest
    dataframe = dataframe.sort_values(metric, ascending=True).reset_index(drop=True)
    colors = [get_model_color(model_name) for model_name in dataframe["model_name"]]
    figure_height = max(5.4, 0.40 * len(dataframe) + 1.9)
    figure, axis = plt.subplots(
        figsize=(10.8, figure_height),
        constrained_layout=True,
    )

    bars = axis.barh(
        dataframe["model_name"],
        dataframe[metric],
        color=colors,
        edgecolor="white",
        linewidth=0.7,
        height=0.48,
    )

    axis.set_title(title, pad=13, fontsize=14, fontweight="semibold")
    axis.set_ylabel("")
    axis.tick_params(axis="y", labelsize=9.2)
    axis.invert_yaxis()
    style_axes(axis, grid_axis="x")

    positive_values = dataframe.loc[dataframe[metric] > 0, metric]

    if metric in {"training_time_seconds", "prediction_time_seconds"} and not positive_values.empty:
        axis.set_xscale("log")
        axis.set_xlabel(f"{ylabel} (log scale)")

        min_positive = float(positive_values.min())
        max_positive = float(positive_values.max())
        axis.set_xlim(min_positive / 1.8, max_positive * 1.75)
        axis.grid(axis="x", which="major", linestyle="--", linewidth=0.65, alpha=0.55)
        axis.grid(axis="x", which="minor", linestyle=":", linewidth=0.45, alpha=0.22)

        for bar, value in zip(bars, dataframe[metric]):
            if value <= 0:
                continue

            axis.text(
                value * 1.08,
                bar.get_y() + bar.get_height() / 2,
                f"{value:.4f}",
                va="center",
                ha="left",
                fontsize=8.6,
                color=TEXT_COLOR,
            )
    else:
        axis.set_xlabel(ylabel)
        max_value = float(dataframe[metric].max())

        if max_value > 0:
            axis.set_xlim(0, max_value * 1.15)

        for bar, value in zip(bars, dataframe[metric]):
            axis.text(
                value + max_value * 0.012 if max_value > 0 else value,
                bar.get_y() + bar.get_height() / 2,
                f"{value:.4f}",
                va="center",
                ha="left",
                fontsize=8.6,
                color=TEXT_COLOR,
            )

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
    dataframe = order_model_dataframe(dataframe)

    if dataframe.empty:
        return None

    metric_count = len(metric_names)
    columns_count = 2 if metric_count > 1 else 1
    rows_count = int(np.ceil(metric_count / columns_count))

    figure, axes = plt.subplots(
        rows_count,
        columns_count,
        figsize=(18, 5.7 * rows_count),
        squeeze=False,
        constrained_layout=True,
    )
    axes = axes.reshape(-1)

    colors = [get_model_color(name) for name in dataframe["model_name"]]
    x = np.arange(len(dataframe))

    for index, metric in enumerate(metric_names):
        axis = axes[index]
        label = METRIC_LABELS.get(metric, metric)

        axis.bar(
            x,
            dataframe[metric],
            color=colors,
            edgecolor="white",
            linewidth=0.7,
            alpha=0.94,
        )

        axis.set_title(label, pad=10, fontsize=13, fontweight="semibold")
        axis.set_ylabel("Score (%)" if as_percent else "Score")
        axis.set_xticks(x)
        axis.set_xticklabels(
            dataframe["model_name"],
            rotation=30,
            ha="right",
            fontsize=8.4,
        )
        style_axes(axis, grid_axis="y")

        if as_percent:
            axis.set_ylim(0, 105)
        else:
            axis.set_ylim(bottom=0)

    for empty_axis in axes[metric_count:]:
        empty_axis.axis("off")

    figure.suptitle(title, fontsize=17, fontweight="semibold")
    save_plot(path)
    return path


def plot_confusion_matrix_group(
    dataframe: pd.DataFrame,
    path: Path,
    title: str,
) -> Optional[Path]:
    if dataframe.empty:
        return None

    dataframe = order_model_dataframe(dataframe)

    model_count = len(dataframe)
    columns_count = 3 if model_count > 2 else model_count
    rows_count = int(np.ceil(model_count / columns_count))

    figure, axes = plt.subplots(
        rows_count,
        columns_count,
        figsize=(columns_count * 4.9, rows_count * 4.25),
        squeeze=False,
        constrained_layout=True,
    )
    axes = axes.reshape(-1)

    last_image = None

    for axis_index, (_, row) in enumerate(dataframe.iterrows()):
        axis = axes[axis_index]

        matrix = np.array(
            [[row["tn"], row["fp"]], [row["fn"], row["tp"]]],
            dtype=float,
        )

        row_sums = matrix.sum(axis=1, keepdims=True)
        normalized_matrix = np.divide(
            matrix,
            row_sums,
            out=np.zeros_like(matrix),
            where=row_sums != 0,
        )

        last_image = axis.imshow(
            normalized_matrix,
            cmap=CONFUSION_CMAP,
            vmin=0,
            vmax=1,
            aspect="equal",
        )

        axis.set_title(
            row["model_name"],
            color=TEXT_COLOR,
            pad=10,
            fontsize=12.5,
            fontweight="semibold",
        )
        axis.set_xticks([0, 1])
        axis.set_yticks([0, 1])
        axis.set_xticklabels(["Normal", "Anomaly"])
        axis.set_yticklabels(["Normal", "Anomaly"])
        axis.set_xlabel("Predicted class")
        axis.set_ylabel("True class")
        axis.tick_params(axis="both", labelsize=9.2)

        for i in range(2):
            for j in range(2):
                count_value = int(matrix[i, j])
                percent_value = normalized_matrix[i, j] * 100
                text_color = "white" if normalized_matrix[i, j] >= 0.55 else TEXT_COLOR

                axis.text(
                    j,
                    i,
                    f"{count_value}\n{percent_value:.1f}%",
                    ha="center",
                    va="center",
                    fontsize=10.5,
                    fontweight="semibold",
                    color=text_color,
                )

    for empty_axis in axes[model_count:]:
        empty_axis.axis("off")

    if last_image is not None:
        colorbar = figure.colorbar(
            last_image,
            ax=[axis for axis in axes[:model_count]],
            fraction=0.025,
            pad=0.02,
        )
        colorbar.set_label("Row-normalized proportion")
        colorbar.ax.tick_params(labelsize=8.5)

    figure.suptitle(title, fontsize=17, fontweight="semibold")
    save_plot(path)
    return path


def plot_confusion_matrices(metrics: pd.DataFrame) -> list[Path]:
    # keep supervised and unsupervised matrices in separate figures
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


def plot_roc_and_pr_curves(
    dataset_id: int,
    metrics: pd.DataFrame,
) -> tuple[Optional[Path], Optional[Path]]:
    if metrics.empty:
        return None, None

    labeled_models = metrics[
        metrics["evaluation_mode"].isin(["labeled", "supervised"])
    ].copy()
    labeled_models = order_model_dataframe(labeled_models)

    if labeled_models.empty:
        return None, None

    roc_path = FIGURES_DIR / "roc_curves.png"
    pr_path = FIGURES_DIR / "precision_recall_curves.png"

    model_groups = [
        (
            "Unsupervised anomaly detection models",
            labeled_models[labeled_models["evaluation_mode"] == "labeled"],
        ),
        (
            "Supervised classification models",
            labeled_models[labeled_models["evaluation_mode"] == "supervised"],
        ),
    ]

    roc_figure, roc_axes = plt.subplots(
        1,
        2,
        figsize=(19, 7.8),
        squeeze=False,
        constrained_layout=True,
    )
    roc_axes = roc_axes.reshape(-1)
    has_roc = False

    for axis, (group_title, group_dataframe) in zip(roc_axes, model_groups):
        group_has_curve = False

        for _, row in group_dataframe.iterrows():
            model_name = row["model_name"]
            curve_data = get_labeled_curve_data(dataset_id, model_name)

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

            axis.plot(
                fpr,
                tpr,
                color=get_model_color(model_name),
                linewidth=2.2,
                label=f"{model_name} (AUC {format_number(row.get('roc_auc'), 3)})",
            )

            group_has_curve = True
            has_roc = True

        axis.plot(
            [0, 1],
            [0, 1],
            linestyle="--",
            linewidth=1.3,
            color=MUTED_TEXT_COLOR,
            label="Chance level (AUC 0.500)",
        )
        axis.set_title(group_title, pad=10, fontsize=13, fontweight="semibold")
        axis.set_xlabel("False Positive Rate")
        axis.set_ylabel("True Positive Rate")
        axis.set_xlim(0, 1)
        axis.set_ylim(0, 1.02)
        style_axes(axis, grid_axis="both")

        if group_has_curve:
            style_legend(axis, location="lower right")

    roc_figure.suptitle(
        "Receiver Operating Characteristic (ROC) curves — chronological test split",
        fontsize=17,
        fontweight="semibold",
    )

    if has_roc:
        roc_figure.savefig(
            roc_path,
            dpi=300,
            bbox_inches="tight",
            facecolor=FIGURE_BACKGROUND,
        )
        plt.close(roc_figure)
    else:
        plt.close(roc_figure)
        roc_path = None

    pr_figure, pr_axes = plt.subplots(
        1,
        2,
        figsize=(19, 7.8),
        squeeze=False,
        constrained_layout=True,
    )
    pr_axes = pr_axes.reshape(-1)
    has_pr = False

    for axis, (group_title, group_dataframe) in zip(pr_axes, model_groups):
        group_has_curve = False
        prevalence_value = None

        for _, row in group_dataframe.iterrows():
            model_name = row["model_name"]
            curve_data = get_labeled_curve_data(dataset_id, model_name)

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

            axis.plot(
                recall,
                precision,
                color=get_model_color(model_name),
                linewidth=2.2,
                label=f"{model_name} (AUC {format_number(row.get('pr_auc'), 3)})",
            )

            if prevalence_value is None:
                prevalence_value = float(np.mean(y_true))

            group_has_curve = True
            has_pr = True

        if prevalence_value is not None:
            axis.axhline(
                prevalence_value,
                linestyle="--",
                linewidth=1.3,
                color=MUTED_TEXT_COLOR,
                label=f"Positive-class baseline ({prevalence_value:.3f})",
            )

        axis.set_title(group_title, pad=10, fontsize=13, fontweight="semibold")
        axis.set_xlabel("Recall")
        axis.set_ylabel("Precision")
        axis.set_xlim(0, 1)
        axis.set_ylim(0, 1.02)
        style_axes(axis, grid_axis="both")

        if group_has_curve:
            style_legend(axis, location="upper right")

    pr_figure.suptitle(
        "Precision–Recall curves — chronological test split",
        fontsize=17,
        fontweight="semibold",
    )

    if has_pr:
        pr_figure.savefig(
            pr_path,
            dpi=300,
            bbox_inches="tight",
            facecolor=FIGURE_BACKGROUND,
        )
        plt.close(pr_figure)
    else:
        plt.close(pr_figure)
        pr_path = None

    return roc_path, pr_path


def plot_anomaly_score_boxplot(
    dataset_id: int,
    path: Path,
) -> Optional[Path]:
    scores = get_anomaly_scores(dataset_id)

    if scores.empty:
        return None

    available_models = set(scores["model_name"].dropna().unique())

    unsupervised_names = [
        name for name in MODEL_ORDER[:9]
        if name in available_models
    ]
    supervised_names = [
        name for name in MODEL_ORDER[9:]
        if name in available_models
    ]

    def collect_group(model_names: list[str]):
        labels = []
        normal_data = []
        anomaly_data = []

        for model_name in model_names:
            curve_data = get_labeled_curve_data(dataset_id, model_name)

            if curve_data.empty:
                continue

            curve_data = curve_data.copy()
            curve_data["anomaly_score"] = pd.to_numeric(
                curve_data["anomaly_score"],
                errors="coerce",
            )
            curve_data = curve_data.dropna(
                subset=["anomaly_score", "original_label"]
            )

            if curve_data.empty:
                continue

            values = curve_data["anomaly_score"].astype(float)
            min_value = float(values.min())
            max_value = float(values.max())

            if max_value == min_value:
                curve_data["normalized_score"] = 0.0
            else:
                curve_data["normalized_score"] = (
                    (values - min_value)
                    / (max_value - min_value)
                )

            normal_values = curve_data.loc[
                curve_data["original_label"].astype(int) == 0,
                "normalized_score",
            ].to_numpy()

            anomaly_values = curve_data.loc[
                curve_data["original_label"].astype(int) == 1,
                "normalized_score",
            ].to_numpy()

            if len(normal_values) == 0 or len(anomaly_values) == 0:
                continue

            labels.append(model_name)
            normal_data.append(normal_values)
            anomaly_data.append(anomaly_values)

        return labels, normal_data, anomaly_data

    unsup_labels, unsup_normal, unsup_anomaly = collect_group(unsupervised_names)
    sup_labels, sup_normal, sup_anomaly = collect_group(supervised_names)

    if not unsup_labels and not sup_labels:
        return None

    figure, axes = plt.subplots(
        2,
        2,
        figsize=(20, 12),
        sharey=True,
        constrained_layout=True,
    )

    plot_specs = [
        (axes[0, 0], unsup_labels, unsup_normal, "Unsupervised models — normal samples"),
        (axes[0, 1], unsup_labels, unsup_anomaly, "Unsupervised models — known anomalies"),
        (axes[1, 0], sup_labels, sup_normal, "Supervised models — normal samples"),
        (axes[1, 1], sup_labels, sup_anomaly, "Supervised models — known anomalies"),
    ]

    for axis, labels, plot_data, title in plot_specs:
        if not labels:
            axis.axis("off")
            continue

        result = axis.boxplot(
            plot_data,
            tick_labels=labels,
            patch_artist=True,
            showfliers=False,
            widths=0.55,
            medianprops={"color": "#222222", "linewidth": 1.5},
            whiskerprops={"color": "#555555", "linewidth": 1.0},
            capprops={"color": "#555555", "linewidth": 1.0},
        )

        for patch, model_name in zip(result["boxes"], labels):
            patch.set_facecolor(get_model_color(model_name))
            patch.set_alpha(0.70)
            patch.set_edgecolor("#333333")
            patch.set_linewidth(0.8)

        axis.set_title(title, pad=10)
        axis.set_ylim(0, 1.02)
        axis.grid(axis="y")
        axis.set_axisbelow(True)
        axis.tick_params(axis="x", rotation=32)

    axes[0, 0].set_ylabel("Normalized anomaly score")
    axes[1, 0].set_ylabel("Normalized anomaly score")

    figure.suptitle(
        "Distribution of normalized anomaly scores — chronological test split"
    )

    save_plot(path)
    return path


def plot_feature_scaling_diagnostics(
    dataset_id: int,
    path: Path,
) -> Optional[Path]:
    dataframe = get_labeled_feature_dataframe(dataset_id)

    if dataframe.empty:
        return None

    train_dataframe, _ = chronological_train_test_split(dataframe)

    if train_dataframe.empty:
        return None

    x_train = train_dataframe[FEATURE_COLUMNS].copy()

    for column in FEATURE_COLUMNS:
        x_train[column] = pd.to_numeric(x_train[column], errors="coerce")

    medians = x_train.median(numeric_only=True)
    x_train = x_train.fillna(medians).fillna(0)

    scaler = StandardScaler()
    scaled_values = scaler.fit_transform(x_train)

    figure, axes = plt.subplots(
        1,
        2,
        figsize=(18, 7.2),
        constrained_layout=True,
    )

    boxplot_kwargs = {
        "tick_labels": FEATURE_COLUMNS,
        "patch_artist": True,
        "showfliers": False,
        "widths": 0.34,
        "medianprops": {"color": "#111827", "linewidth": 1.6},
        "whiskerprops": {"color": "#6B7280", "linewidth": 0.9},
        "capprops": {"color": "#6B7280", "linewidth": 0.9},
    }

    raw_values = [
        x_train[column].to_numpy()
        for column in FEATURE_COLUMNS
    ]

    scaled_feature_values = [
        scaled_values[:, index]
        for index in range(len(FEATURE_COLUMNS))
    ]

    raw_result = axes[0].boxplot(
        raw_values,
        **boxplot_kwargs,
    )

    scaled_result = axes[1].boxplot(
        scaled_feature_values,
        **boxplot_kwargs,
    )

    apply_boxplot_style(raw_result, FEATURE_COLORS)
    apply_boxplot_style(scaled_result, FEATURE_COLORS)

    for axis in axes:
        axis.tick_params(
            axis="x",
            rotation=28,
            labelsize=8.7,
        )
        style_axes(axis, grid_axis="y")

    axes[0].set_title(
        "Before StandardScaler",
        pad=10,
        fontsize=13,
        fontweight="semibold",
    )
    axes[0].set_ylabel("Feature value (symmetric log scale)")

    # symlog keeps small-value features visible without deleting large-value features
    axes[0].set_yscale("symlog", linthresh=1.0)

    axes[1].set_title(
        "After StandardScaler",
        pad=10,
        fontsize=13,
        fontweight="semibold",
    )
    axes[1].set_ylabel("Standardized value")

    # most standardized values should be visually comparable around zero
    scaled_limit = np.nanpercentile(
        np.abs(scaled_values),
        99,
    )

    if np.isfinite(scaled_limit) and scaled_limit > 0:
        axes[1].set_ylim(
            -scaled_limit * 1.15,
            scaled_limit * 1.15,
        )

    figure.suptitle(
        "Feature distributions before and after scaling — training split only",
        fontsize=17,
        fontweight="semibold",
    )

    save_plot(path)
    return path


def plot_supervised_learning_curves(
    dataset_id: int,
    path: Path,
) -> Optional[Path]:
    dataframe = get_labeled_feature_dataframe(dataset_id)

    if dataframe.empty or dataframe["original_label"].nunique() < 2:
        return None

    outer_train, _ = chronological_train_test_split(dataframe)
    fit_dataframe, validation_dataframe = chronological_train_validation_split(
        outer_train
    )

    if (
        fit_dataframe.empty
        or validation_dataframe.empty
        or fit_dataframe["original_label"].nunique() < 2
        or validation_dataframe["original_label"].nunique() < 2
    ):
        return None

    train_fractions = [0.20, 0.35, 0.50, 0.65, 0.80, 1.00]
    has_curve = False

    figure, axis = plt.subplots(figsize=(16, 8), constrained_layout=True)

    for model_config in SUPERVISED_MODELS:
        model_name = model_config["name"]
        x_points = []
        validation_points = []

        for fraction in train_fractions:
            subset_size = max(10, int(len(fit_dataframe) * fraction))
            subset = fit_dataframe.iloc[:subset_size].copy()

            if subset["original_label"].nunique() < 2:
                continue

            x_train, x_validation = prepare_model_input(
                model_config,
                subset,
                validation_dataframe,
            )

            y_train = subset["original_label"].astype(int).to_numpy()
            y_validation = (
                validation_dataframe["original_label"]
                .astype(int)
                .to_numpy()
            )

            model = model_config["build_model"]()
            model.fit(x_train, y_train)
            predictions = model.predict(x_validation).astype(int)

            x_points.append(subset_size)
            validation_points.append(
                safe_f1_score(y_validation, predictions)
            )

        if x_points:
            axis.plot(
                x_points,
                validation_points,
                marker="o",
                markersize=6,
                linewidth=2.3,
                color=get_model_color(model_name),
                label=model_name,
            )
            has_curve = True

    if not has_curve:
        plt.close(figure)
        return None

    axis.set_title("Validation F1-score as a function of training-set size", pad=12)
    axis.set_xlabel("Number of training examples")
    axis.set_ylabel("Validation F1-score")
    axis.set_ylim(0, 1.05)
    axis.grid()
    axis.set_axisbelow(True)
    axis.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=3,
        frameon=True,
        facecolor="white",
        framealpha=0.95,
    )

    save_plot(path)
    return path


def plot_gradient_boosting_staged_performance(
    dataset_id: int,
    path: Path,
) -> Optional[Path]:
    dataframe = get_labeled_feature_dataframe(dataset_id)

    if dataframe.empty or dataframe["original_label"].nunique() < 2:
        return None

    outer_train, _ = chronological_train_test_split(dataframe)
    fit_dataframe, validation_dataframe = chronological_train_validation_split(
        outer_train
    )

    if (
        fit_dataframe.empty
        or validation_dataframe.empty
        or fit_dataframe["original_label"].nunique() < 2
        or validation_dataframe["original_label"].nunique() < 2
    ):
        return None

    model_config = next(
        item for item in SUPERVISED_MODELS
        if item["name"] == GRADIENT_BOOSTING_NAME
    )

    x_train, x_validation = prepare_model_input(
        model_config,
        fit_dataframe,
        validation_dataframe,
    )

    y_train = fit_dataframe["original_label"].astype(int).to_numpy()
    y_validation = (
        validation_dataframe["original_label"]
        .astype(int)
        .to_numpy()
    )

    model = model_config["build_model"]()
    model.fit(x_train, y_train)

    stages = []
    train_losses = []
    validation_losses = []

    train_stages = model.staged_predict_proba(x_train)
    validation_stages = model.staged_predict_proba(x_validation)

    for stage_index, (train_probabilities, validation_probabilities) in enumerate(
        zip(train_stages, validation_stages),
        start=1,
    ):
        if (
            stage_index == 1
            or stage_index % 5 == 0
            or stage_index == model.n_estimators
        ):
            train_probabilities = np.asarray(train_probabilities)[:, 1]
            validation_probabilities = np.asarray(validation_probabilities)[:, 1]

            stages.append(stage_index)
            train_losses.append(
                log_loss(y_train, train_probabilities, labels=[0, 1])
            )
            validation_losses.append(
                log_loss(y_validation, validation_probabilities, labels=[0, 1])
            )

    if not stages:
        return None

    best_index = int(np.argmin(validation_losses))
    best_stage = stages[best_index]
    best_validation_loss = validation_losses[best_index]

    figure, axis = plt.subplots(figsize=(14, 7), constrained_layout=True)

    axis.plot(
        stages,
        train_losses,
        marker="o",
        markersize=5,
        linewidth=2.3,
        color=get_model_color("Isolation Forest"),
        label="Training log loss",
    )
    axis.plot(
        stages,
        validation_losses,
        marker="o",
        markersize=5,
        linewidth=2.3,
        color=get_model_color("Gradient Boosting"),
        label="Validation log loss",
    )
    axis.axvline(
        best_stage,
        linestyle="--",
        linewidth=1.5,
        color="#666666",
        label=f"Minimum validation loss (stage {best_stage})",
    )
    axis.scatter(
        [best_stage],
        [best_validation_loss],
        s=75,
        color=get_model_color("Gradient Boosting"),
        zorder=5,
    )

    axis.set_title(
        "Gradient Boosting learning dynamics across boosting stages",
        pad=12,
    )
    axis.set_xlabel("Number of boosting stages")
    axis.set_ylabel("Log loss")
    axis.grid()
    axis.set_axisbelow(True)
    axis.legend(
        loc="upper right",
        frameon=True,
        facecolor="white",
        framealpha=0.95,
    )

    save_plot(path)
    return path



def plot_feature_correlation_heatmap(
    feature_dataframe: pd.DataFrame,
    path: Path,
) -> Optional[Path]:
    if feature_dataframe.empty:
        return None

    numeric_dataframe = feature_dataframe.copy()

    for column in FEATURE_COLUMNS:
        numeric_dataframe[column] = pd.to_numeric(numeric_dataframe[column], errors="coerce")

    correlation = numeric_dataframe[FEATURE_COLUMNS].corr()

    if correlation.empty:
        return None

    figure, axis = plt.subplots(figsize=(10.5, 9), constrained_layout=True)
    image = axis.imshow(
        correlation,
        cmap=CORRELATION_CMAP,
        vmin=-1,
        vmax=1,
        aspect="equal",
    )

    axis.set_xticks(np.arange(len(FEATURE_COLUMNS)))
    axis.set_yticks(np.arange(len(FEATURE_COLUMNS)))
    axis.set_xticklabels(FEATURE_COLUMNS, rotation=35, ha="right", fontsize=9)
    axis.set_yticklabels(FEATURE_COLUMNS, fontsize=9)
    axis.set_title("Feature correlation matrix", pad=12, fontsize=14, fontweight="semibold")

    for i in range(len(FEATURE_COLUMNS)):
        for j in range(len(FEATURE_COLUMNS)):
            value = correlation.iloc[i, j]
            if pd.isna(value):
                continue

            text_color = "white" if abs(value) >= 0.65 else TEXT_COLOR
            axis.text(
                j,
                i,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=8.1,
                color=text_color,
            )

    colorbar = figure.colorbar(image, ax=axis, fraction=0.045, pad=0.04)
    colorbar.set_label("Pearson correlation")
    colorbar.ax.tick_params(labelsize=8.5)

    save_plot(path)
    return path


def remove_obsolete_figures() -> None:
    # kept for compatibility with earlier versions
    clear_figures_directory()


def generate_figures(dataset_id: int, metrics: pd.DataFrame) -> list[Path]:
    # start from a clean figures folder on every report run
    clear_figures_directory()

    generated_paths = []

    figure_paths = [
        plot_feature_scaling_diagnostics(
            dataset_id,
            FIGURES_DIR / "feature_scaling_diagnostics.png",
        ),
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
        plot_feature_correlation_heatmap(
            get_feature_dataframe(dataset_id),
            FIGURES_DIR / "feature_correlation_heatmap.png",
        ),
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
    # keep figure links relative to the reports folder
    return Path(os.path.relpath(path, start=REPORTS_DIR)).as_posix()


def build_report() -> str:
    # build one report from database metrics, tables and figures
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
        "- Missing temperature and humidity values are kept during cleaning and are filled later using values learned only from the training data",
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
        "| Unsupervised anomaly detection | Isolation Forest, Local Outlier Factor, One-Class SVM, DBSCAN, K-Means, Gaussian Mixture Model, PCA, HBOS, ECOD | Used when anomaly labels are not available |",
        "| Supervised classification | Logistic Regression, Decision Tree, Random Forest, Gradient Boosting, KNN Classifier | Used when labels exist and the model can be evaluated directly |",
        "",
        "## 7. Evaluation Methodology",
        "",
        "The dataset is split chronologically: the first 70% of records are used for model development and the last 30% are kept as the final test set. Missing-value replacement and model scaling are fitted only on the training data.",
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
            "The figures support the metric table with feature diagnostics, model comparisons, confusion matrices and ROC and Precision-Recall curves. Classification curves use anomaly scores stored by the main model pipeline on the chronological test split.",
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
