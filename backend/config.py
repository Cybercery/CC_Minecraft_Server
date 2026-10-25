from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 5173
    DOCKER_GID: int = 10001

    # MinIO
    MINIO_ENDPOINT: str = "http://minio:9090"
    MINIO_ROOT_USER: str = "admin"
    MINIO_ROOT_PASSWORD: str = "password123"
    MINIO_BUCKET: str = "minecraft-backups"
    MINIO_CONSOLE_PORT: int = 9001
    MINIO_APP_ACCESS_KEY: Optional[str] = None
    MINIO_APP_SECRET_KEY: Optional[str] = None

    # Minecraft Server
    MC_VERSION: str = "1.20.4"
    MC_MEMORY: str = "2G"
    MC_MAX_PLAYERS: int = 20
    MC_CONTAINER_NAME: str = "cloud-minecraft"
    MC_PUBLIC_ADDRESS: str = "localhost:25565"
    MINECRAFT_ONLINE_MODE: bool = True
    RCON_PASSWORD: Optional[str] = None
    PLUGIN_API_KEY: Optional[str] = None
    CODE_HMAC_SECRET: Optional[str] = None

    # Firebase & Auth
    FIREBASE_PROJECT_ID: str = "demo-project"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    FIREBASE_AUTH_EMULATOR_HOST: Optional[str] = None
    BOOTSTRAP_ADMIN_EMAIL: str = "admin@example.com"

    # Dashboard & CORS
    DASHBOARD_URL: str = "http://localhost:5173"
    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:8080"

    # Metrics & Backups & Alerts
    METRICS_INTERVAL_SECONDS: int = 30
    METRICS_RETENTION_DAYS: int = 7
    BACKUP_SCHEDULE_CRON: str = "0 3 * * *"
    BACKUP_RETENTION_COUNT: int = 10
    CPU_ALERT_THRESHOLD: float = 80.0
    MEM_ALERT_THRESHOLD: float = 90.0
    DISK_ALERT_THRESHOLD: float = 85.0
    VERIFICATION_CODE_TTL_SECONDS: int = 300

settings = Settings()

