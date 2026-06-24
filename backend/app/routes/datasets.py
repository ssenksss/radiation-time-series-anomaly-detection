from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.dataset_upload_service import (
    get_datasets_from_database,
    upload_dataset_and_run_pipeline,
)

router = APIRouter(tags=["datasets"])


@router.get("/datasets")
def read_datasets():
    return get_datasets_from_database()


@router.post("/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)):
    try:
        return await upload_dataset_and_run_pipeline(file)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))
