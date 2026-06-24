from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.services.database_settings_service import (
    get_settings_from_database,
    update_threshold_in_database,
    update_active_model_in_database,
)
from app.services.pipeline_service import start_pipeline_in_background


router = APIRouter(tags=["settings"])


class ThresholdUpdateRequest(BaseModel):
    threshold: float


class ModelUpdateRequest(BaseModel):
    activeModel: str


@router.get("/settings")
def read_settings():
    try:
        return get_settings_from_database()
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))

@router.put("/settings/threshold")
def update_threshold(
        payload: ThresholdUpdateRequest,
        background_tasks: BackgroundTasks,
):
    try:
        settings = update_threshold_in_database(payload.threshold)
        pipeline_status = start_pipeline_in_background(
            background_tasks,
            mode="threshold-update",
        )

        return {
            **settings,
            "pipeline": pipeline_status,
        }
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))

@router.put("/settings/model")
def update_model(payload: ModelUpdateRequest):
    try:
        return update_active_model_in_database(payload.activeModel)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))