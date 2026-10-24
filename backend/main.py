from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.database import get_connection
from backend.services.minio_client import check_bucket_health
from backend.config import settings
import logging

logging.basicConfig(level=logging.INFO)

from backend.routes.server import router as server_router
from backend.routes.auth import router as auth_router
from backend.routes.users import router as users_router
from backend.routes.minecraft import router as minecraft_router
from backend.routes.backups import router as backups_router
from backend.routes.metrics import router as metrics_router
from storage.scheduler import start_backup_scheduler

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

app = FastAPI(title="Minecraft Cloud API")

origins = [o.strip() for o in settings.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

app.add_middleware(SecurityHeadersMiddleware)

app.include_router(server_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(minecraft_router)
app.include_router(backups_router)
app.include_router(metrics_router)

@app.on_event("startup")
def on_startup():
    start_backup_scheduler()

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
