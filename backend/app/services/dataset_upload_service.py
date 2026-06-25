from pathlib import Path
from datetime import datetime
import subprocess
import sys
from typing import Dict, Any

from fastapi import UploadFile

from app.database.connection import fetch_all, fetch_one, execute_query


ROOT_DIR = Path(__file__).resolve().parents[3]
UPLOAD_DIR = ROOT_DIR / "ml" / "datasets" / "uploads"
PIPELINE_SCRIPT = ROOT_DIR / "ml" / "scripts" / "run_ml_pipeline.py"


def get_active_dataset_id() -> int:
    row = fetch_one(
        """
        SELECT value
        FROM app_settings
        WHERE key = 'active_dataset_id';
        """
    )

    if not row:
        return 1

    return int(row["value"])


async def save_uploaded_dataset(file: UploadFile) -> Path:
    if not file.filename:
        raise RuntimeError("Uploaded file does not have a filename.")

    filename = file.filename.lower()

    if not (filename.endswith(".csv") or filename.endswith(".zip")):
        raise RuntimeError("Only CSV files and ZIP files containing CSV files are supported.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = Path(file.filename).name.replace(" ", "_")
    destination = UPLOAD_DIR / f"{timestamp}_{safe_filename}"

    content = await file.read()
    destination.write_bytes(content)

    return destination


def run_pipeline_for_dataset(dataset_path: Path) -> Dict[str, Any]:
    if not PIPELINE_SCRIPT.exists():
        raise RuntimeError(f"Pipeline script not found: {PIPELINE_SCRIPT}")

    command = [
        sys.executable,
        str(PIPELINE_SCRIPT),
        "--file",
        str(dataset_path),
    ]

    result = subprocess.run(
        command,
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Pipeline failed.\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )

    active_dataset_id = get_active_dataset_id()

    return {
        "success": True,
        "activeDatasetId": active_dataset_id,
        "pipelineOutput": result.stdout,
    }


def update_dataset_display_name(dataset_id: int, original_filename: str) -> None:
    clean_filename = Path(original_filename).name
    clean_name = Path(clean_filename).stem

    execute_query(
        """
        UPDATE datasets
        SET name = %s,
            original_filename = %s
        WHERE id = %s;
        """,
        (clean_name, clean_filename, dataset_id),
    )


async def upload_dataset_and_run_pipeline(file: UploadFile) -> Dict[str, Any]:
    original_filename = Path(file.filename or "uploaded_dataset.csv").name

    saved_path = await save_uploaded_dataset(file)
    pipeline_result = run_pipeline_for_dataset(saved_path)

    active_dataset_id = pipeline_result["activeDatasetId"]
    update_dataset_display_name(active_dataset_id, original_filename)

    return {
        "message": "Dataset uploaded and processed successfully.",
        "filename": original_filename,
        "savedFilename": saved_path.name,
        "savedPath": str(saved_path),
        **pipeline_result,
    }


def get_datasets_from_database() -> list:
    rows = fetch_all(
        """
        SELECT
            id,
            name,
            original_filename,
            source_type,
            uploaded_at,
            row_count,
            status,
            is_active
        FROM datasets
        ORDER BY uploaded_at DESC;
        """
    )

    datasets = []

    for row in rows:
        datasets.append(
            {
                "id": int(row["id"]),
                "name": row["name"],
                "originalFilename": row["original_filename"],
                "sourceType": row["source_type"],
                "uploadedAt": row["uploaded_at"].strftime("%Y-%m-%d %H:%M:%S"),
                "rowCount": int(row["row_count"]),
                "status": row["status"],
                "isActive": bool(row["is_active"]),
            }
        )

    return datasets