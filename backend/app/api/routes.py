from sqlite3 import Connection

from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.database import get_connection
from app.core.log import get_logger, log_event

router = APIRouter()
LOGGER = get_logger(__name__)
MODULE_FILE = __file__


@router.get("/health")
def health(connection: Connection = Depends(get_connection)):
    function_name = "health"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
    )

    try:
        connection.execute("SELECT 1").fetchone()
        response = {
            "status": "ok",
            "engine": "sqlite",
            "path": str(settings.sqlite_database_path),
        }
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            result=response["status"],
        )
        return response
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            error=str(error),
            exc_info=True,
        )
        raise
