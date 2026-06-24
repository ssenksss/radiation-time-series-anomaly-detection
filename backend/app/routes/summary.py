from fastapi import APIRouter

from app.services.database_summary_service import get_summary_from_database

router = APIRouter(tags=["summary"])


@router.get("/summary")
def read_summary():
    return get_summary_from_database()
