from fastapi import APIRouter
from app.services.data_service import get_measurements_df

router = APIRouter(tags=["measurements"])


def _row_to_response(row) -> dict:
    return {
        "timestamp": row["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
        "radiationLevel": round(float(row["radiationLevel"]), 4),
        "sensorId": str(row["sensorId"]),
        "location": str(row["location"]),
        "temperature": None if row["temperature"] is None else round(float(row["temperature"]), 2),
        "humidity": None if row["humidity"] is None else round(float(row["humidity"]), 2),
        "isAnomaly": bool(row["isAnomaly"]),
        "anomalyScore": round(float(row["anomalyScore"]), 3),
        "anomalyType": str(row["anomalyType"]),
        "status": str(row["status"]),
    }


@router.get("/measurements")
def get_measurements(limit: int = 1000):
    df = get_measurements_df()

    # Za chart ne treba slati svih 10k tacaka.
    # Default je poslednjih 1000, ali mozes: /measurements?limit=10000
    if limit and limit > 0:
        df = df.tail(limit)

    return [_row_to_response(row) for _, row in df.iterrows()]