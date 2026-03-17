from fastapi import APIRouter

from app.core.config import settings
from app.core.log import get_logger, log_event

router = APIRouter()
LOGGER = get_logger(__name__)
MODULE_FILE = __file__


@router.get("/")
def root():
    function_name = "root"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
    )

    try:
        response = {
            "message": "Corpustar backend is running",
            "database": "sqlite",
            "database_path": str(settings.sqlite_database_path),
        }
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            result=response["message"],
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
