from sqlite3 import Connection

from app.core.config import settings
from app.core.log import get_logger, log_event
from app.infrastructure.db.connection import connection_scope

DOCUMENTS_TABLE_NAME = "documents"
DOCUMENTS_TEXT_CHAR_COUNT_COLUMN = "text_char_count"
PROCESSINGS_TABLE_NAME = "processings"
DOCUMENT_SENTENCES_TABLE_NAME = "document_sentences"
DOCUMENT_SENTENCES_LEMMA_TEXT_COLUMN = "lemma_text"
PROCESSINGS_DOC_TYPE_CREATED_AT_INDEX_NAME = "idx_processings_doc_type_created_at"
DOCUMENT_SENTENCES_PROCESSING_DOC_START_OFFSET_INDEX_NAME = (
    "idx_document_sentences_processing_doc_start_offset"
)

LOGGER = get_logger(__name__)
MODULE_FILE = __file__


def init_schema(connection: Connection | None = None) -> None:
    function_name = "init_schema"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
    )
    if connection is None:
        settings.sqlite_database_path.parent.mkdir(parents=True, exist_ok=True)
        with connection_scope() as scoped_connection:
            _init_schema_with_connection(scoped_connection)
        return

    _init_schema_with_connection(connection)


def _init_schema_with_connection(connection: Connection) -> None:
    function_name = "_init_schema_with_connection"
    try:
        if not _table_exists(connection, DOCUMENTS_TABLE_NAME):
            _create_documents_table(connection)
        if not _table_exists(connection, PROCESSINGS_TABLE_NAME):
            _create_processings_table(connection)
        if not _table_exists(connection, DOCUMENT_SENTENCES_TABLE_NAME):
            _create_document_sentences_table(connection)

        _create_index_if_not_exists(
            connection=connection,
            index_name=PROCESSINGS_DOC_TYPE_CREATED_AT_INDEX_NAME,
            table_name=PROCESSINGS_TABLE_NAME,
            columns=("doc_id", "type", "created_at"),
        )
        _create_index_if_not_exists(
            connection=connection,
            index_name=DOCUMENT_SENTENCES_PROCESSING_DOC_START_OFFSET_INDEX_NAME,
            table_name=DOCUMENT_SENTENCES_TABLE_NAME,
            columns=("processing_id", "doc_id", "start_offset"),
        )

        _validate_schema(connection)
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name="init_schema",
            result="schema_initialized",
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


def _create_documents_table(connection: Connection) -> None:
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


def _create_processings_table(connection: Connection) -> None:
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


def _create_document_sentences_table(connection: Connection) -> None:
    connection.execute(
        f"""
        CREATE TABLE {DOCUMENT_SENTENCES_TABLE_NAME} (
            id TEXT PRIMARY KEY,
            doc_id TEXT NOT NULL,
            processing_id TEXT NOT NULL,
            start_offset INTEGER NOT NULL,
            end_offset INTEGER NOT NULL,
            {DOCUMENT_SENTENCES_LEMMA_TEXT_COLUMN} TEXT NULL,
            FOREIGN KEY (doc_id) REFERENCES {DOCUMENTS_TABLE_NAME}(id) ON DELETE CASCADE,
            FOREIGN KEY (processing_id) REFERENCES {PROCESSINGS_TABLE_NAME}(id) ON DELETE CASCADE,
            CHECK(start_offset >= 0),
            CHECK(end_offset > start_offset)
        )
        """
    )
    connection.commit()


def _create_index_if_not_exists(
    connection: Connection,
    index_name: str,
    table_name: str,
    columns: tuple[str, ...],
) -> None:
    columns_sql = ", ".join(columns)
    connection.execute(
        f"""
        CREATE INDEX IF NOT EXISTS {index_name}
        ON {table_name} ({columns_sql})
        """
    )
    connection.commit()


def _validate_schema(connection: Connection) -> None:
    required_tables = (
        DOCUMENTS_TABLE_NAME,
        PROCESSINGS_TABLE_NAME,
        DOCUMENT_SENTENCES_TABLE_NAME,
    )
    for table_name in required_tables:
        if not _table_exists(connection, table_name):
            raise RuntimeError(f"Missing required sqlite table: {table_name}")

    required_indexes = (
        PROCESSINGS_DOC_TYPE_CREATED_AT_INDEX_NAME,
        DOCUMENT_SENTENCES_PROCESSING_DOC_START_OFFSET_INDEX_NAME,
    )
    for index_name in required_indexes:
        if not _index_exists(connection, index_name):
            raise RuntimeError(f"Missing required sqlite index: {index_name}")

    required_columns = {
        DOCUMENTS_TABLE_NAME: (
            "id",
            "filename",
            "display_name",
            "note",
            "source_path",
            "text_path",
            "file_type",
            "file_size",
            "created_at",
            "updated_at",
        ),
        PROCESSINGS_TABLE_NAME: (
            "id",
            "doc_id",
            "type",
            "state",
            "created_at",
            "updated_at",
            "error_message",
            "meta_json",
        ),
        DOCUMENT_SENTENCES_TABLE_NAME: (
            "id",
            "doc_id",
            "processing_id",
            "start_offset",
            "end_offset",
            DOCUMENT_SENTENCES_LEMMA_TEXT_COLUMN,
        ),
    }

    for table_name, column_names in required_columns.items():
        for column_name in column_names:
            if not _column_exists(connection, table_name, column_name):
                raise RuntimeError(
                    f"Missing required sqlite column: {table_name}.{column_name}"
                )


def _table_exists(connection: Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _index_exists(connection: Connection, index_name: str) -> bool:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'index' AND name = ?",
        (index_name,),
    ).fetchone()
    return row is not None


def _column_exists(connection: Connection, table_name: str, column_name: str) -> bool:
    rows = connection.execute(f'PRAGMA table_info("{table_name}")').fetchall()
    return any(row["name"] == column_name for row in rows)
