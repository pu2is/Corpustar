from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.core.config import settings
from app.core.db import init_db
from app.core.log import get_logger, log_event

LOGGER = get_logger(__name__)
MODULE_FILE = __file__

log_event(
    LOGGER,
    stage="CALL",
    module_file=MODULE_FILE,
    function_name="init_db",
)
init_db()
log_event(
    LOGGER,
    stage="OK",
    module_file=MODULE_FILE,
    function_name="init_db",
    result="initialized",
)

app = FastAPI(title=settings.api_title)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
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
