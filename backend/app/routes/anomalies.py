from fastapi import APIRouter

from app.services.data_service import get_measurements_df
from app.services.anomaly_service import get_anomalies
from app.routes.measurements import _row_to_response

router = APIRouter(tags=["anomalies"])


@router.get("/anomalies")
def read_anomalies(limit: int = 200):
    df = get_measurements_df()
    anomalies = get_anomalies(df)

    if limit and limit > 0:
        anomalies = anomalies.head(limit)

    return [_row_to_response(row) for _, row in anomalies.iterrows()]