from fastapi import APIRouter, BackgroundTasks, Query

from app.services.pipeline_service import (
    get_pipeline_status,
    start_pipeline_in_background,
)


router = APIRouter(tags=["pipeline"])


@router.get("/pipeline/status")
def read_pipeline_status():
    return get_pipeline_status()


@router.post("/pipeline/run")
def run_pipeline(
        background_tasks: BackgroundTasks,
        mode: str = Query(default="threshold-update"),
):
    return start_pipeline_in_background(background_tasks, mode=mode)