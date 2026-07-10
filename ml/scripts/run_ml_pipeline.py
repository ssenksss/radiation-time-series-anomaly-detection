from pathlib import Path
import argparse
import sys
import time
from typing import Any, Callable, Dict, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "ml" / "scripts"

for import_path in (PROJECT_ROOT, SCRIPTS_DIR):
    if str(import_path) not in sys.path:
        sys.path.append(str(import_path))

from db import fetch_one
from ingest_data import ingest_csv, DEFAULT_CSV_PATH
from data_preprocessing import preprocess_active_dataset
from create_features import create_features_for_active_dataset
from ml.models.unsupervised.train_isolation_forest import train_model_for_active_dataset
from ml.models.unsupervised.train_lof import train_lof_for_active_dataset
from ml.models.unsupervised.train_one_class_svm import train_one_class_svm_for_active_dataset
from ml.models.unsupervised.train_dbscan import train_dbscan_for_active_dataset
from ml.models.unsupervised.train_kmeans_distance import train_kmeans_distance_for_active_dataset
from ml.models.unsupervised.train_gaussian_mixture import train_gaussian_mixture_for_active_dataset
from ml.models.unsupervised.train_pca_reconstruction import train_pca_reconstruction_for_active_dataset
from ml.models.unsupervised.train_hbos import train_hbos_for_active_dataset
from ml.models.unsupervised.train_ecod import train_ecod_for_active_dataset
from evaluate_model import evaluate_active_dataset


TimingDict = Dict[str, Any]
TrainFunction = Callable[[], Optional[TimingDict]]


def get_active_model_id() -> str:
    # read selected model from app (settings)
    row = fetch_one("SELECT value FROM app_settings WHERE key = 'active_model';")

    if not row:
        return "isolation_forest"

    value = str(row["value"]).strip().lower().replace("-", "_").replace(" ", "_")

    if value in {"isolation_forest", "isolation", "isolationforest", "iforest"}:
        return "isolation_forest"

    if value in {"local_outlier_factor", "localoutlierfactor", "lof"}:
        return "lof"

    if value in {"one_class_svm", "oneclasssvm", "ocsvm"}:
        return "one_class_svm"

    if value in {"dbscan"}:
        return "dbscan"

    if value in {"kmeans_distance", "kmeans", "k_means_distance"}:
        return "kmeans_distance"

    if value in {"gaussian_mixture", "gaussian_mixture_model", "gmm"}:
        return "gaussian_mixture"

    if value in {"pca_reconstruction", "pca_reconstruction_error", "pca"}:
        return "pca_reconstruction"

    if value in {"hbos"}:
        return "hbos"

    if value in {"ecod"}:
        return "ecod"

    return "isolation_forest"


def normalize_timing(raw_timing: Optional[TimingDict]) -> TimingDict:
    # keep the same timing format for all models
    if not raw_timing:
        return {
            "training_time_seconds": None,
            "prediction_time_seconds": None,
        }

    return {
        "training_time_seconds": raw_timing.get("training_time_seconds"),
        "prediction_time_seconds": raw_timing.get("prediction_time_seconds"),
    }


def run_model(model_label: str, train_function: TrainFunction) -> Tuple[str, TimingDict]:
    # run one model and return timing for the report
    timing = train_function()
    return model_label, normalize_timing(timing)


UNSUPERVISED_MODEL_STEPS: list[Tuple[str, str, TrainFunction]] = [
    ("Isolation Forest", "train Isolation Forest and write anomaly_results", train_model_for_active_dataset),
    ("Local Outlier Factor", "train Local Outlier Factor and write anomaly_results", train_lof_for_active_dataset),
    ("One-Class SVM", "train One-Class SVM and write anomaly_results", train_one_class_svm_for_active_dataset),
    ("DBSCAN", "train DBSCAN and write anomaly_results", train_dbscan_for_active_dataset),
    ("K-Means Distance", "train K-Means Distance and write anomaly_results", train_kmeans_distance_for_active_dataset),
    ("Gaussian Mixture Model", "train Gaussian Mixture Model and write anomaly_results", train_gaussian_mixture_for_active_dataset),
    ("PCA Reconstruction Error", "train PCA Reconstruction Error and write anomaly_results", train_pca_reconstruction_for_active_dataset),
    ("HBOS", "train HBOS and write anomaly_results", train_hbos_for_active_dataset),
    ("ECOD", "train ECOD and write anomaly_results", train_ecod_for_active_dataset),
]


ACTIVE_MODEL_REGISTRY: dict[str, Tuple[str, TrainFunction]] = {
    "isolation_forest": ("Isolation Forest", train_model_for_active_dataset),
    "lof": ("Local Outlier Factor", train_lof_for_active_dataset),
    "one_class_svm": ("One-Class SVM", train_one_class_svm_for_active_dataset),
    "dbscan": ("DBSCAN", train_dbscan_for_active_dataset),
    "kmeans_distance": ("K-Means Distance", train_kmeans_distance_for_active_dataset),
    "gaussian_mixture": ("Gaussian Mixture Model", train_gaussian_mixture_for_active_dataset),
    "pca_reconstruction": ("PCA Reconstruction Error", train_pca_reconstruction_for_active_dataset),
    "hbos": ("HBOS", train_hbos_for_active_dataset),
    "ecod": ("ECOD", train_ecod_for_active_dataset),
}


def train_active_model_only() -> Tuple[str, TimingDict]:
    active_model = get_active_model_id()
    model_label, train_function = ACTIVE_MODEL_REGISTRY.get(
        active_model,
        ACTIVE_MODEL_REGISTRY["isolation_forest"],
    )

    return run_model(model_label, train_function)


def run_full_pipeline(csv_path: Path, skip_ingest: bool = False) -> None:
    started_at = time.time()
    model_timings: dict[str, TimingDict] = {}

    print("=" * 60)
    print("Radiation Monitoring ML Pipeline")
    print("Mode: FULL")
    print("=" * 60)

    # full mode rebuilds the complete data and model pipeline
    if skip_ingest:
        print("Step 1/13 skipped: using current active dataset")
    else:
        print("Step 1/13: ingest CSV into PostgreSQL raw_measurements")
        ingest_csv(csv_path)

    print("\nStep 2/13: raw_measurements -> clean_measurements")
    preprocess_active_dataset()

    print("\nStep 3/13: clean_measurements -> feature_measurements")
    create_features_for_active_dataset()

    # unsupervised models are trained first because labels are not required
    for step_number, (model_label, step_title, train_function) in enumerate(
            UNSUPERVISED_MODEL_STEPS,
            start=4,
    ):
        print(f"\nStep {step_number}/13: {step_title}")
        _, timing = run_model(model_label, train_function)
        model_timings[model_label] = timing

    print("\nStep 13/13: evaluate unsupervised models and write model_metrics")
    evaluate_active_dataset(
        model_names=list(model_timings.keys()),
        model_timings=model_timings,
    )

    elapsed = round(time.time() - started_at, 2)

    print("\n" + "=" * 60)
    print("Full pipeline completed successfully.")
    print(f"Execution time: {elapsed} seconds")
    print("=" * 60)


def run_threshold_update_pipeline() -> None:
    started_at = time.time()

    print("=" * 60)
    print("Radiation Monitoring ML Pipeline")
    print("Mode: THRESHOLD UPDATE")
    print("=" * 60)

    print("Step 1/2: train only the active model")
    # threshold update is faster because it avoids rebuilding all layers
    active_model_label, timing = train_active_model_only()

    print("\nStep 2/2: evaluate only the active model")
    evaluate_active_dataset(
        model_names=[active_model_label],
        model_timings={active_model_label: timing},
    )

    elapsed = round(time.time() - started_at, 2)

    print("\n" + "=" * 60)
    print("Fast threshold-update pipeline completed successfully.")
    print(f"Active model: {active_model_label}")
    print(f"Execution time: {elapsed} seconds")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Run radiation monitoring ELT and ML pipeline.")

    parser.add_argument("--file", type=str, default=str(DEFAULT_CSV_PATH))
    parser.add_argument("--skip-ingest", action="store_true")
    parser.add_argument(
        "--mode",
        type=str,
        default="full",
        choices=["full", "threshold-update"],
    )

    args = parser.parse_args()

    if args.mode == "threshold-update":
        run_threshold_update_pipeline()
        return

    run_full_pipeline(Path(args.file), args.skip_ingest)


if __name__ == "__main__":
    main()
