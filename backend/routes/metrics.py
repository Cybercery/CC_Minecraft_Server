from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from backend.auth import AuthenticatedUser, require_permission
from monitoring.metrics import metrics_service
from monitoring.collector import collector

router = APIRouter(prefix="/metrics", tags=["metrics"])

class CurrentMetricsResponse(BaseModel):
    cpu_percent: float
    memory_bytes: int
    memory_total_bytes: int
    memory_percent: float
    disk_used_bytes: int
    disk_total_bytes: int
    disk_percent: float
    online_players: int
    is_running: int

class MetricSnapshot(BaseModel):
    id: int
    cpu_percent: float
    memory_bytes: int
    memory_percent: float
    disk_used_bytes: int
    disk_total_bytes: int
    disk_percent: float
    online_players: int
    is_running: int
    timestamp: str

@router.get("/current", response_model=CurrentMetricsResponse)
def get_current_metrics(
    user: AuthenticatedUser = Depends(require_permission("metrics:read"))
):
    return metrics_service.get_latest_metrics()

@router.get("/history", response_model=List[MetricSnapshot])
def get_metrics_history(
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=200, ge=1, le=1000),
    user: AuthenticatedUser = Depends(require_permission("metrics:read"))
):
    return metrics_service.get_historical_metrics(hours=hours, limit=limit)

@router.post("/collect", response_model=CurrentMetricsResponse)
def trigger_metric_snapshot(
    user: AuthenticatedUser = Depends(require_permission("metrics:read"))
):
    return collector.record_snapshot()
