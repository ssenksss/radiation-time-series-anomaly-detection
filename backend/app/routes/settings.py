from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.database_settings_service import (
    get_settings_from_database,
    update_threshold_in_database,
    update_active_model_in_database,
)


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
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.put("/settings/threshold")
def update_threshold(
    payload: ThresholdUpdateRequest,
):
    try:
        return update_threshold_in_database(
            payload.threshold
        )
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.put("/settings/model")
def update_model(
    payload: ModelUpdateRequest,
):
    try:
        return update_active_model_in_database(
            payload.activeModel
        )
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )