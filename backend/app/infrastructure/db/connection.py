from collections.abc import Generator
from contextlib import contextmanager
from sqlite3 import Connection, Row, connect

from app.core.config import settings
from app.core.log import get_logger, log_event

LOGGER = get_logger(__name__)
MODULE_FILE = __file__


def open_connection() -> Connection:
    function_name = "open_connection"
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
        if foreign_keys_row is None or int(foreign_keys_row[0]) != 1:
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


@contextmanager
def connection_scope() -> Generator[Connection, None, None]:
    function_name = "connection_scope"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
    )
    connection = open_connection()
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
