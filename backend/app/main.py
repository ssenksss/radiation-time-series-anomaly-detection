from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.settings import router as settings_router
from app.routes.measurements import router as measurements_router
from app.routes.anomalies import router as anomalies_router
from app.routes.summary import router as summary_router
from app.routes.model_info import router as model_info_router
from app.routes.datasets import router as datasets_router
from app.routes.pipeline import router as pipeline_router


app = FastAPI(
    title="Radiation Monitoring API",
    description="FastAPI backend for radiation time-series anomaly detection prototype.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(measurements_router)
app.include_router(anomalies_router)
app.include_router(summary_router)
app.include_router(model_info_router)
app.include_router(settings_router)
app.include_router(datasets_router)
app.include_router(pipeline_router)


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "Radiation Monitoring API is running",
        "endpoints": [
            "/measurements",
            "/anomalies",
            "/summary",
            "/model-info",
            "/settings",
            "/settings/threshold",
            "/datasets",
            "/datasets/upload",
            "/pipeline/status",
            "/pipeline/run",
        ],
    }