from sqlite3 import Connection

from app.core.config import settings
from app.core.log import get_logger, log_event
from app.infrastructure.db.connection import connection_scope

LOGGER = get_logger(__name__)
MODULE_FILE = __file__


def apply_migrations(connection: Connection | None = None) -> None:
    function_name = "apply_migrations"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
    )
    if connection is None:
        settings.sqlite_database_path.parent.mkdir(parents=True, exist_ok=True)
        with connection_scope() as scoped_connection:
            _apply_migrations_with_connection(scoped_connection)
        return

    _apply_migrations_with_connection(connection)


def _apply_migrations_with_connection(connection: Connection) -> None:
    # Keep the parameter for API symmetry with init_schema.
    _ = connection
    function_name = "_apply_migrations_with_connection"
    log_event(
        LOGGER,
        stage="OK",
        module_file=MODULE_FILE,
        function_name=function_name,
        result="skipped_no_auto_migrations",
    )
    log_event(
        LOGGER,
        stage="OK",
        module_file=MODULE_FILE,
        function_name="apply_migrations",
        result="no_migration_required",
    )


__all__ = ["apply_migrations"]
