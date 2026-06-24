from datetime import datetime
from pathlib import Path
import subprocess
import sys
import threading
import uuid
from typing import Any, Dict, Optional

from fastapi import BackgroundTasks

from app.database.connection import fetch_one


ROOT_DIR = Path(__file__).resolve().parents[3]
PIPELINE_SCRIPT = ROOT_DIR / "ml" / "scripts" / "run_ml_pipeline.py"

VALID_PIPELINE_MODES = {"full", "threshold-update"}

_status_lock = threading.Lock()

_pipeline_status: Dict[str, Any] = {
    "jobId": None,
    "status": "idle",
    "mode": None,
    "message": "ML pipeline is idle.",
    "startedAt": None,
    "finishedAt": None,
    "activeDatasetId": None,
    "stdoutTail": "",
    "stderrTail": "",
    "errorMessage": None,
}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _tail(text: str, limit: int = 4000) -> str:
    if not text:
        return ""

    return text[-limit:]


def get_active_dataset_id() -> Optional[int]:
    row = fetch_one(
        """
        SELECT value
        FROM app_settings
        WHERE key = 'active_dataset_id';
        """
    )

    if not row:
        return None

    return int(row["value"])


def get_pipeline_status() -> Dict[str, Any]:
    with _status_lock:
        return dict(_pipeline_status)


def _set_pipeline_status(**updates: Any) -> None:
    with _status_lock:
        _pipeline_status.update(updates)


def _normalize_mode(mode: str) -> str:
    normalized = mode.strip().lower()

    if normalized not in VALID_PIPELINE_MODES:
        return "threshold-update"

    return normalized


def _run_pipeline_job(job_id: str, mode: str) -> None:
    mode = _normalize_mode(mode)

    if not PIPELINE_SCRIPT.exists():
        _set_pipeline_status(
            jobId=job_id,
            status="failed",
            mode=mode,
            message="ML pipeline script was not found.",
            finishedAt=_now(),
            errorMessage=f"Pipeline script not found: {PIPELINE_SCRIPT}",
        )
        return

    command = [
        sys.executable,
        str(PIPELINE_SCRIPT),
        "--mode",
        mode,
    ]

    try:
        _set_pipeline_status(
            jobId=job_id,
            status="running",
            mode=mode,
            message=f"ML pipeline is running in background. Mode: {mode}.",
            startedAt=_now(),
            finishedAt=None,
            errorMessage=None,
            stdoutTail="",
            stderrTail="",
            activeDatasetId=get_active_dataset_id(),
        )

        result = subprocess.run(
            command,
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            timeout=600,
        )

        if result.returncode != 0:
            _set_pipeline_status(
                jobId=job_id,
                status="failed",
                mode=mode,
                message="ML pipeline failed.",
                finishedAt=_now(),
                stdoutTail=_tail(result.stdout),
                stderrTail=_tail(result.stderr),
                errorMessage=result.stderr or "ML pipeline failed.",
                activeDatasetId=get_active_dataset_id(),
            )
            return

        _set_pipeline_status(
            jobId=job_id,
            status="success",
            mode=mode,
            message="ML pipeline completed successfully.",
            finishedAt=_now(),
            stdoutTail=_tail(result.stdout),
            stderrTail=_tail(result.stderr),
            errorMessage=None,
            activeDatasetId=get_active_dataset_id(),
        )

    except subprocess.TimeoutExpired as error:
        _set_pipeline_status(
            jobId=job_id,
            status="failed",
            mode=mode,
            message="ML pipeline timed out.",
            finishedAt=_now(),
            stdoutTail=_tail(error.stdout or ""),
            stderrTail=_tail(error.stderr or ""),
            errorMessage="ML pipeline timed out after 10 minutes.",
            activeDatasetId=get_active_dataset_id(),
        )

    except Exception as error:
        _set_pipeline_status(
            jobId=job_id,
            status="failed",
            mode=mode,
            message="ML pipeline failed unexpectedly.",
            finishedAt=_now(),
            errorMessage=str(error),
            activeDatasetId=get_active_dataset_id(),
        )


def start_pipeline_in_background(
        background_tasks: BackgroundTasks,
        mode: str = "threshold-update",
) -> Dict[str, Any]:
    mode = _normalize_mode(mode)
    current_status = get_pipeline_status()

    if current_status["status"] == "running":
        return {
            **current_status,
            "message": "ML pipeline is already running.",
        }

    job_id = str(uuid.uuid4())

    _set_pipeline_status(
        jobId=job_id,
        status="running",
        mode=mode,
        message=f"ML pipeline started in background. Mode: {mode}.",
        startedAt=_now(),
        finishedAt=None,
        activeDatasetId=get_active_dataset_id(),
        stdoutTail="",
        stderrTail="",
        errorMessage=None,
    )

    background_tasks.add_task(_run_pipeline_job, job_id, mode)

    return get_pipeline_status()