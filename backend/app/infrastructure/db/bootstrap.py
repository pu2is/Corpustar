from app.core.config import settings
from app.core.log import get_logger, log_event
from app.infrastructure.db.migrations import apply_migrations
from app.infrastructure.db.schema import init_schema

LOGGER = get_logger(__name__)
MODULE_FILE = __file__


def ensure_database_ready() -> None:
    function_name = "ensure_database_ready"
    database_path = settings.sqlite_database_path
    missing_or_empty_db = (not database_path.exists()) or database_path.stat().st_size == 0

    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        sqlite_database_path=str(database_path),
        missing_or_empty_db=missing_or_empty_db,
    )

    # Always run both steps: this keeps startup idempotent and works for both new and legacy DBs.
    init_schema()
    apply_migrations()

    log_event(
        LOGGER,
        stage="OK",
        module_file=MODULE_FILE,
        function_name=function_name,
        result="initialized" if missing_or_empty_db else "verified",
    )

