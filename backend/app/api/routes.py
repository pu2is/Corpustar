from sqlite3 import Connection

from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.database import get_connection

router = APIRouter()


@router.get("/health")
def health(connection: Connection = Depends(get_connection)):
    connection.execute("SELECT 1").fetchone()

    return {
        "status": "ok",
        "engine": "sqlite",
        "path": str(settings.sqlite_database_path),
    }
