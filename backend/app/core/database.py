from collections.abc import Generator
from sqlite3 import Connection, Row, connect

from app.core.config import settings
from app.core.log import get_logger, log_event

LOGGER = get_logger(__name__)
MODULE_FILE = __file__


def initialize_database() -> None:
    function_name = "initialize_database"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        sqlite_database_path=str(settings.sqlite_database_path),
    )

    try:
        settings.sqlite_database_path.parent.mkdir(parents=True, exist_ok=True)

        with _open_connection() as connection:
            connection.commit()

        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            result="initialized",
        )
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


def get_connection() -> Generator[Connection, None, None]:
    function_name = "get_connection"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
    )
    connection = _open_connection()

    try:
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            result="connection_opened",
        )
        yield connection
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
    finally:
        connection.close()
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            result="connection_closed",
        )


def _open_connection() -> Connection:
    function_name = "_open_connection"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        sqlite_database_path=str(settings.sqlite_database_path),
    )
    try:
        connection = connect(settings.sqlite_database_path)
        connection.row_factory = Row
        connection.execute("PRAGMA foreign_keys = ON;")
        foreign_keys_row = connection.execute("PRAGMA foreign_keys;").fetchone()
        if foreign_keys_row is None or foreign_keys_row[0] != 1:
            raise RuntimeError("Failed to enable sqlite foreign keys pragma.")
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            result="opened_with_foreign_keys",
        )
        return connection
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            sqlite_database_path=str(settings.sqlite_database_path),
            error=str(error),
            exc_info=True,
        )
        raise
