from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.settings_service import (
    get_settings,
    update_active_model,
    update_threshold,
)
from app.services.data_service import refresh_dataset_cache

router = APIRouter(tags=["settings"])


class ThresholdUpdateRequest(BaseModel):
    threshold: float = Field(ge=0, le=10)


class ActiveModelUpdateRequest(BaseModel):
    activeModel: str


@router.get("/settings")
def read_settings():
    return get_settings()


@router.put("/settings/threshold")
def update_threshold_route(payload: ThresholdUpdateRequest):
    settings = update_threshold(payload.threshold)

    # Kada se promeni threshold, ponovo se računaju anomaly podaci
    refresh_dataset_cache()

    return settings


@router.put("/settings/model")
def update_active_model_route(payload: ActiveModelUpdateRequest):
    try:
        settings = update_active_model(payload.activeModel)
        return settings
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))