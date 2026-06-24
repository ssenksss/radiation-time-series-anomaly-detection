from pathlib import Path
import argparse
import time

from db import fetch_one
from ingest_data import ingest_csv, DEFAULT_CSV_PATH
from data_preprocessing import preprocess_active_dataset
from create_features import create_features_for_active_dataset
from train_isolation_forest import train_model_for_active_dataset
from train_lof import train_lof_for_active_dataset
from evaluate_model import evaluate_active_dataset


ACTIVE_MODEL_TO_LABEL = {
    "isolation_forest": "Isolation Forest",
    "lof": "Local Outlier Factor",
    "local_outlier_factor": "Local Outlier Factor",
}


def get_active_model_id() -> str:
    row = fetch_one(
        """
        SELECT value
        FROM app_settings
        WHERE key = 'active_model';
        """
    )

    if not row:
        return "isolation_forest"

    value = str(row["value"]).strip().lower().replace("-", "_").replace(" ", "_")

    if value in {"isolation", "isolationforest", "iforest"}:
        return "isolation_forest"

    if value in {"local_outlier_factor", "lof"}:
        return "lof"

    return "isolation_forest"


def train_active_model_only() -> str:
    active_model = get_active_model_id()

    if active_model == "lof":
        print("Fast mode: training active model only -> Local Outlier Factor")
        train_lof_for_active_dataset()
        return "Local Outlier Factor"

    print("Fast mode: training active model only -> Isolation Forest")
    train_model_for_active_dataset()
    return "Isolation Forest"


def run_full_pipeline(csv_path: Path, skip_ingest: bool = False) -> None:
    started_at = time.time()

    print("=" * 60)
    print("Radiation Monitoring ML Pipeline")
    print("Mode: FULL")
    print("=" * 60)

    if skip_ingest:
        print("Step 1/6 skipped: using current active dataset")
    else:
        print("Step 1/6: ingest CSV into PostgreSQL raw_measurements")
        ingest_csv(csv_path)

    print("\nStep 2/6: raw_measurements -> clean_measurements")
    preprocess_active_dataset()

    print("\nStep 3/6: clean_measurements -> feature_measurements")
    create_features_for_active_dataset()

    print("\nStep 4/6: train Isolation Forest and write anomaly_results")
    train_model_for_active_dataset()

    print("\nStep 5/6: train Local Outlier Factor and write anomaly_results")
    train_lof_for_active_dataset()

    print("\nStep 6/6: evaluate all models and write model_metrics")
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
    parser = argparse.ArgumentParser(
        description="Run radiation monitoring ELT and ML pipeline."
    )

    parser.add_argument(
        "--file",
        type=str,
        default=str(DEFAULT_CSV_PATH),
        help="Path to the CSV file that should be processed.",
    )

    parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Skip CSV ingest and use the current active dataset from the database.",
    )

    parser.add_argument(
        "--mode",
        type=str,
        default="full",
        choices=["full", "threshold-update"],
        help="Pipeline mode. Use 'full' for dataset upload and 'threshold-update' for settings changes.",
    )

    args = parser.parse_args()

    if args.mode == "threshold-update":
        run_threshold_update_pipeline()
        return

    run_full_pipeline(
        csv_path=Path(args.file),
        skip_ingest=args.skip_ingest,
    )


if __name__ == "__main__":
    main()