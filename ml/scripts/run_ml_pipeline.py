from pathlib import Path
import argparse
import time

from db import fetch_one
from ingest_data import ingest_csv, DEFAULT_CSV_PATH
from data_preprocessing import preprocess_active_dataset
from create_features import create_features_for_active_dataset
from train_isolation_forest import train_model_for_active_dataset
from train_lof import train_lof_for_active_dataset
from train_one_class_svm import train_one_class_svm_for_active_dataset
from train_elliptic_envelope import train_elliptic_envelope_for_active_dataset
from train_dbscan import train_dbscan_for_active_dataset
from train_kmeans_distance import train_kmeans_distance_for_active_dataset
from train_gaussian_mixture import train_gaussian_mixture_for_active_dataset
from train_pca_reconstruction import train_pca_reconstruction_for_active_dataset
from train_hbos import train_hbos_for_active_dataset
from train_ecod import train_ecod_for_active_dataset
from evaluate_model import evaluate_active_dataset


def get_active_model_id() -> str:
    row = fetch_one("SELECT value FROM app_settings WHERE key = 'active_model';")
    if not row:
        return "isolation_forest"

    value = str(row["value"]).strip().lower().replace("-", "_").replace(" ", "_")

    if value in {"isolation", "isolationforest", "iforest"}:
        return "isolation_forest"
    if value in {"local_outlier_factor", "lof"}:
        return "lof"
    if value in {"one_class_svm", "oneclasssvm", "ocsvm"}:
        return "one_class_svm"
    if value in {"elliptic_envelope", "ellipticenvelope"}:
        return "elliptic_envelope"
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


def train_active_model_only() -> str:
    active_model = get_active_model_id()

    if active_model == "lof":
        train_lof_for_active_dataset()
        return "Local Outlier Factor"

    if active_model == "one_class_svm":
        train_one_class_svm_for_active_dataset()
        return "One-Class SVM"

    if active_model == "elliptic_envelope":
        train_elliptic_envelope_for_active_dataset()
        return "Elliptic Envelope"

    if active_model == "dbscan":
        train_dbscan_for_active_dataset()
        return "DBSCAN"

    if active_model == "kmeans_distance":
        train_kmeans_distance_for_active_dataset()
        return "K-Means Distance"

    if active_model == "gaussian_mixture":
        train_gaussian_mixture_for_active_dataset()
        return "Gaussian Mixture Model"

    if active_model == "pca_reconstruction":
        train_pca_reconstruction_for_active_dataset()
        return "PCA Reconstruction Error"

    if active_model == "hbos":
        train_hbos_for_active_dataset()
        return "HBOS"

    if active_model == "ecod":
        train_ecod_for_active_dataset()
        return "ECOD"

    train_model_for_active_dataset()
    return "Isolation Forest"


def run_full_pipeline(csv_path: Path, skip_ingest: bool = False) -> None:
    started_at = time.time()

    print("=" * 60)
    print("Radiation Monitoring ML Pipeline")
    print("Mode: FULL")
    print("=" * 60)

    if skip_ingest:
        print("Step 1/14 skipped: using current active dataset")
    else:
        print("Step 1/14: ingest CSV into PostgreSQL raw_measurements")
        ingest_csv(csv_path)

    print("\nStep 2/14: raw_measurements -> clean_measurements")
    preprocess_active_dataset()

    print("\nStep 3/14: clean_measurements -> feature_measurements")
    create_features_for_active_dataset()

    print("\nStep 4/14: train Isolation Forest and write anomaly_results")
    train_model_for_active_dataset()

    print("\nStep 5/14: train Local Outlier Factor and write anomaly_results")
    train_lof_for_active_dataset()

    print("\nStep 6/14: train One-Class SVM and write anomaly_results")
    train_one_class_svm_for_active_dataset()

    print("\nStep 7/14: train Elliptic Envelope and write anomaly_results")
    train_elliptic_envelope_for_active_dataset()

    print("\nStep 8/14: train DBSCAN and write anomaly_results")
    train_dbscan_for_active_dataset()

    print("\nStep 9/14: train K-Means Distance and write anomaly_results")
    train_kmeans_distance_for_active_dataset()

    print("\nStep 10/14: train Gaussian Mixture Model and write anomaly_results")
    train_gaussian_mixture_for_active_dataset()

    print("\nStep 11/14: train PCA Reconstruction Error and write anomaly_results")
    train_pca_reconstruction_for_active_dataset()

    print("\nStep 12/14: train HBOS and write anomaly_results")
    train_hbos_for_active_dataset()

    print("\nStep 13/14: train ECOD and write anomaly_results")
    train_ecod_for_active_dataset()

    print("\nStep 14/14: evaluate all models and write model_metrics")
    evaluate_active_dataset()

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
    active_model_label = train_active_model_only()

    print("\nStep 2/2: evaluate only the active model")
    evaluate_active_dataset(model_names=[active_model_label])

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