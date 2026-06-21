from fastapi import APIRouter

from app.services.data_service import get_measurements_df
from app.services.summary_service import calculate_summary

router = APIRouter(tags=["summary"])


@router.get("/summary")
def read_summary():
    df = get_measurements_df()
    return calculate_summary(df)