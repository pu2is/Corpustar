from app.core.config import settings
from app.infrastructure.repositories.health_repository import ping_database


def get_health_status() -> dict:
    ping_database()
    return {
        "status": "ok",
        "engine": "sqlite",
        "path": str(settings.sqlite_database_path),
    }
