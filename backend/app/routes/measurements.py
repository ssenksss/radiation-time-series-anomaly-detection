from fastapi import APIRouter

from app.services.database_measurement_service import get_measurements_from_database

router = APIRouter(tags=["measurements"])


@router.get("/measurements")
def get_measurements(limit: int = 1000):
    return get_measurements_from_database(limit=limit)
