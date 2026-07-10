from typing import Optional

from fastapi import APIRouter

from app.services.database_model_service import (
    get_model_curves_from_database,
    get_model_info_from_database,
)

router = APIRouter(tags=["model"])


@router.get("/model-info")
def read_model_info(
    modelA: Optional[str] = None,
    modelB: Optional[str] = None,
):
    return get_model_info_from_database(modelA, modelB)


@router.get("/model-curves")
def read_model_curves(
    modelA: Optional[str] = None,
    modelB: Optional[str] = None,
):
    return get_model_curves_from_database(modelA, modelB)
