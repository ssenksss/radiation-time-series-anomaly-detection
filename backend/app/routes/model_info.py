from typing import Optional

from fastapi import APIRouter

from app.services.data_service import get_measurements_df
from app.services.model_service import get_model_info
from app.services.settings_service import get_active_model

router = APIRouter(tags=["model-info"])


@router.get("/model-info")
def read_model_info(modelA: Optional[str] = None, modelB: str = "isolation_forest"):
    df = get_measurements_df()

    active_model = modelA or get_active_model()

    return get_model_info(df, active_model, modelB)