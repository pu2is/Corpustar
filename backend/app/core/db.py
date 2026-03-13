from collections.abc import Generator
from sqlite3 import Connection, Row, connect

from app.core.config import settings
from app.core.log import get_logger, log_event

DOCUMENTS_TABLE_NAME = "documents"
DOCUMENTS_TEXT_CHAR_COUNT_COLUMN = "text_char_count"
PROCESSINGS_TABLE_NAME = "processings"
DOCUMENT_SENTENCES_TABLE_NAME = "document_sentences"
PROCESSINGS_DOC_TYPE_CREATED_AT_INDEX_NAME = "idx_processings_doc_type_created_at"
DOCUMENT_SENTENCES_PROCESSING_DOC_START_OFFSET_INDEX_NAME = (
    "idx_document_sentences_processing_doc_start_offset"
)
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
            if not _table_exists(connection, DOCUMENTS_TABLE_NAME):
                init_document_table(connection)
                log_event(
                    LOGGER,
                    stage="OK",
                    module_file=MODULE_FILE,
                    function_name=function_name,
                    table_name=DOCUMENTS_TABLE_NAME,
                    result="table_initialized",
                )
            elif _column_exists(
                connection,
                DOCUMENTS_TABLE_NAME,
                DOCUMENTS_TEXT_CHAR_COUNT_COLUMN,
            ):
                log_event(
                    LOGGER,
                    stage="OK",
                    module_file=MODULE_FILE,
                    function_name=function_name,
                    table_name=DOCUMENTS_TABLE_NAME,
                    column_name=DOCUMENTS_TEXT_CHAR_COUNT_COLUMN,
                    result="table_and_column_already_exist",
                )
            else:
                connection.execute(
                    f"""
                    ALTER TABLE {DOCUMENTS_TABLE_NAME}
                    ADD COLUMN {DOCUMENTS_TEXT_CHAR_COUNT_COLUMN} INTEGER NOT NULL DEFAULT 0
                    """
                )
                connection.commit()
                log_event(
                    LOGGER,
                    stage="OK",
                    module_file=MODULE_FILE,
                    function_name=function_name,
                    table_name=DOCUMENTS_TABLE_NAME,
                    column_name=DOCUMENTS_TEXT_CHAR_COUNT_COLUMN,
                    result="column_added",
                )

            _ensure_processings_schema(connection)
            _ensure_document_sentences_schema(connection)
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
                {DOCUMENTS_TEXT_CHAR_COUNT_COLUMN} INTEGER NOT NULL,
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


def init_processings_table(connection: Connection) -> None:
    function_name = "init_processings_table"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        table_name=PROCESSINGS_TABLE_NAME,
    )
    try:
        connection.execute(
            f"""
            CREATE TABLE {PROCESSINGS_TABLE_NAME} (
                id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                type TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                error_message TEXT NULL,
                meta_json TEXT NULL,
                FOREIGN KEY (doc_id) REFERENCES {DOCUMENTS_TABLE_NAME}(id) ON DELETE CASCADE,
                CHECK(state IN ('running', 'succeed', 'failed'))
            )
            """
        )
        connection.commit()
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            table_name=PROCESSINGS_TABLE_NAME,
            result="created",
        )
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            table_name=PROCESSINGS_TABLE_NAME,
            error=str(error),
            exc_info=True,
        )
        raise


def init_document_sentences_table(connection: Connection) -> None:
    function_name = "init_document_sentences_table"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        table_name=DOCUMENT_SENTENCES_TABLE_NAME,
    )
    try:
        connection.execute(
            f"""
            CREATE TABLE {DOCUMENT_SENTENCES_TABLE_NAME} (
                id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                processing_id TEXT NOT NULL,
                start_offset INTEGER NOT NULL,
                end_offset INTEGER NOT NULL,
                FOREIGN KEY (doc_id) REFERENCES {DOCUMENTS_TABLE_NAME}(id) ON DELETE CASCADE,
                FOREIGN KEY (processing_id) REFERENCES {PROCESSINGS_TABLE_NAME}(id) ON DELETE CASCADE,
                CHECK(start_offset >= 0),
                CHECK(end_offset > start_offset)
            )
            """
        )
        connection.commit()
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            table_name=DOCUMENT_SENTENCES_TABLE_NAME,
            result="created",
        )
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            table_name=DOCUMENT_SENTENCES_TABLE_NAME,
            error=str(error),
            exc_info=True,
        )
        raise


def _ensure_processings_schema(connection: Connection) -> None:
    function_name = "_ensure_processings_schema"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        table_name=PROCESSINGS_TABLE_NAME,
    )
    try:
        if not _table_exists(connection, PROCESSINGS_TABLE_NAME):
            init_processings_table(connection)
            log_event(
                LOGGER,
                stage="OK",
                module_file=MODULE_FILE,
                function_name=function_name,
                table_name=PROCESSINGS_TABLE_NAME,
                result="table_initialized",
            )
        else:
            log_event(
                LOGGER,
                stage="OK",
                module_file=MODULE_FILE,
                function_name=function_name,
                table_name=PROCESSINGS_TABLE_NAME,
                result="table_already_exists",
            )

        _create_index_if_not_exists(
            connection=connection,
            index_name=PROCESSINGS_DOC_TYPE_CREATED_AT_INDEX_NAME,
            table_name=PROCESSINGS_TABLE_NAME,
            columns=("doc_id", "type", "created_at"),
        )
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            table_name=PROCESSINGS_TABLE_NAME,
            result="schema_ensured",
        )
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            table_name=PROCESSINGS_TABLE_NAME,
            error=str(error),
            exc_info=True,
        )
        raise


def _ensure_document_sentences_schema(connection: Connection) -> None:
    function_name = "_ensure_document_sentences_schema"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        table_name=DOCUMENT_SENTENCES_TABLE_NAME,
    )
    try:
        if not _table_exists(connection, DOCUMENT_SENTENCES_TABLE_NAME):
            init_document_sentences_table(connection)
            log_event(
                LOGGER,
                stage="OK",
                module_file=MODULE_FILE,
                function_name=function_name,
                table_name=DOCUMENT_SENTENCES_TABLE_NAME,
                result="table_initialized",
            )
        else:
            log_event(
                LOGGER,
                stage="OK",
                module_file=MODULE_FILE,
                function_name=function_name,
                table_name=DOCUMENT_SENTENCES_TABLE_NAME,
                result="table_already_exists",
            )

        _create_index_if_not_exists(
            connection=connection,
            index_name=DOCUMENT_SENTENCES_PROCESSING_DOC_START_OFFSET_INDEX_NAME,
            table_name=DOCUMENT_SENTENCES_TABLE_NAME,
            columns=("processing_id", "doc_id", "start_offset"),
        )
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            table_name=DOCUMENT_SENTENCES_TABLE_NAME,
            result="schema_ensured",
        )
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            table_name=DOCUMENT_SENTENCES_TABLE_NAME,
            error=str(error),
            exc_info=True,
        )
        raise


def _create_index_if_not_exists(
    connection: Connection,
    index_name: str,
    table_name: str,
    columns: tuple[str, ...],
) -> None:
    function_name = "_create_index_if_not_exists"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        table_name=table_name,
        index_name=index_name,
        columns=",".join(columns),
    )
    try:
        columns_sql = ", ".join(columns)
        connection.execute(
            f"""
            CREATE INDEX IF NOT EXISTS {index_name}
            ON {table_name} ({columns_sql})
            """
        )
        connection.commit()
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            table_name=table_name,
            index_name=index_name,
            result="index_ensured",
        )
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            table_name=table_name,
            index_name=index_name,
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


def _column_exists(connection: Connection, table_name: str, column_name: str) -> bool:
    function_name = "_column_exists"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        table_name=table_name,
        column_name=column_name,
    )
    try:
        rows = connection.execute(f'PRAGMA table_info("{table_name}")').fetchall()
        result = any(row["name"] == column_name for row in rows)
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            table_name=table_name,
            column_name=column_name,
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
            column_name=column_name,
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
