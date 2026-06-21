from fastapi import APIRouter

from app.services.data_service import get_measurements_df
from app.services.model_service import get_model_info

router = APIRouter(tags=["model-info"])


@router.get("/model-info")
def read_model_info():
    df = get_measurements_df()
    return get_model_info(df)