from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.database import get_connection
from backend.services.minio_client import check_bucket_health
import logging

logging.basicConfig(level=logging.INFO)

from backend.routes.server import router as server_router
from backend.routes.auth import router as auth_router
from backend.routes.users import router as users_router

app = FastAPI(title="Minecraft Cloud API")
app.include_router(server_router)
app.include_router(auth_router)
app.include_router(users_router)

class HealthCheckResponse(BaseModel):
    status: str
    db_schema_version: int
    minio_healthy: bool

@app.get("/health", response_model=HealthCheckResponse)
def health_check():
    db_version = 0
    try:
        conn = get_connection()
        cursor = conn.execute("SELECT MAX(version) as v FROM schema_version")
        row = cursor.fetchone()
        if row and row['v'] is not None:
            db_version = row['v']
        conn.close()
    except Exception as e:
        logging.error(f"DB health check failed: {e}")
        raise HTTPException(status_code=503, detail="Database degraded")

    minio_healthy = check_bucket_health()
    if not minio_healthy:
        raise HTTPException(status_code=503, detail="MinIO degraded")

    return HealthCheckResponse(
        status="ok",
        db_schema_version=db_version,
        minio_healthy=True
    )
