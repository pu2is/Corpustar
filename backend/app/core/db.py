from collections.abc import Generator
from sqlite3 import Connection, Row, connect

from app.core.config import settings
from app.core.log import get_logger, log_event

DOCUMENTS_TABLE_NAME = "documents"
LOGGER = get_logger(__name__)
MODULE_FILE = __file__


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


def init_db() -> None:
    function_name = "init_db"
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
            if _table_exists(connection, DOCUMENTS_TABLE_NAME):
                log_event(
                    LOGGER,
                    stage="OK",
                    module_file=MODULE_FILE,
                    function_name=function_name,
                    table_name=DOCUMENTS_TABLE_NAME,
                    result="table_already_exists",
                )
                return

            init_document_table(connection)
            log_event(
                LOGGER,
                stage="OK",
                module_file=MODULE_FILE,
                function_name=function_name,
                table_name=DOCUMENTS_TABLE_NAME,
                result="table_initialized",
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


def init_document_table(connection: Connection) -> None:
    function_name = "init_document_table"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        table_name=DOCUMENTS_TABLE_NAME,
    )
    try:
        connection.execute(
            f"""
            CREATE TABLE {DOCUMENTS_TABLE_NAME} (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                display_name TEXT NOT NULL,
                note TEXT NOT NULL,
                source_path TEXT NOT NULL,
                text_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.commit()
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            table_name=DOCUMENTS_TABLE_NAME,
            result="created",
        )
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            table_name=DOCUMENTS_TABLE_NAME,
            error=str(error),
            exc_info=True,
        )
        raise


def _table_exists(connection: Connection, table_name: str) -> bool:
    function_name = "_table_exists"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        table_name=table_name,
    )
    try:
        row = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
        result = row is not None
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            table_name=table_name,
            result=result,
        )
        return result
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            table_name=table_name,
            error=str(error),
            exc_info=True,
        )
        raise


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
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            result="opened",
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
