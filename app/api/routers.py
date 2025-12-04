from fastapi import APIRouter
from app.services.metrics_service import MetricsService

router = APIRouter()

@router.get("/metrics")
def get_metrics():
    return MetricsService.get_metrics()
