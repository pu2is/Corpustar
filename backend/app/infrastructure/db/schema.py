from sqlite3 import Connection

from app.core.config import settings
from app.core.log import get_logger, log_event
from app.infrastructure.db.connection import connection_scope

DOCUMENTS_TABLE_NAME = "documents"
DOCUMENTS_TEXT_CHAR_COUNT_COLUMN = "text_char_count"
PROCESSINGS_TABLE_NAME = "processings"
DOCUMENT_SENTENCES_TABLE_NAME = "document_sentences"
DOCUMENT_SENTENCES_SOURCE_TEXT_COLUMN = "source_text"
DOCUMENT_SENTENCES_LEMMA_TEXT_COLUMN = "lemma_text"
PROCESSINGS_DOC_TYPE_CREATED_AT_INDEX_NAME = "idx_processings_doc_type_created_at"
RULES_TABLE_NAME = "rules"
RULE_FVG_TABLE_NAME = "rule_fvg"
RULE_FVG_RULE_ID_INDEX_NAME = "idx_rule_fvg_rule_id"
DOCUMENT_SENTENCES_PROCESSING_DOC_START_OFFSET_INDEX_NAME = (
    "idx_document_sentences_processing_doc_start_offset"
)
DOCUMENT_SENTENCES_SOURCE_TEXT_LOCK_TRIGGER_NAME = (
    "trg_document_sentences_source_text_locked"
)

EXPECTED_TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    DOCUMENTS_TABLE_NAME: (
        "id",
        "filename",
        "display_name",
        "note",
        "source_path",
        "text_path",
        DOCUMENTS_TEXT_CHAR_COUNT_COLUMN,
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
        DOCUMENT_SENTENCES_SOURCE_TEXT_COLUMN,
        DOCUMENT_SENTENCES_LEMMA_TEXT_COLUMN,
    ),
    RULES_TABLE_NAME: (
        "id",
        "type",
        "path",
    ),
    RULE_FVG_TABLE_NAME: (
        "id",
        "rule_id",
        "verb",
        "phrase",
    ),
}

EXPECTED_INDEXES = (
    PROCESSINGS_DOC_TYPE_CREATED_AT_INDEX_NAME,
    DOCUMENT_SENTENCES_PROCESSING_DOC_START_OFFSET_INDEX_NAME,
    RULE_FVG_RULE_ID_INDEX_NAME,
)

EXPECTED_TRIGGERS = (
    DOCUMENT_SENTENCES_SOURCE_TEXT_LOCK_TRIGGER_NAME,
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
        if _is_uninitialized_database(connection):
            _create_schema(connection)
            result = "schema_created"
        else:
            _validate_schema(connection)
            result = "schema_validated"

        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name="init_schema",
            result=result,
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


def _is_uninitialized_database(connection: Connection) -> bool:
    return len(_list_user_tables(connection)) == 0


def _create_schema(connection: Connection) -> None:
    connection.executescript(
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
        );

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
        );

        CREATE TABLE {DOCUMENT_SENTENCES_TABLE_NAME} (
            id TEXT PRIMARY KEY,
            doc_id TEXT NOT NULL,
            processing_id TEXT NOT NULL,
            start_offset INTEGER NOT NULL,
            end_offset INTEGER NOT NULL,
            {DOCUMENT_SENTENCES_SOURCE_TEXT_COLUMN} TEXT NOT NULL,
            {DOCUMENT_SENTENCES_LEMMA_TEXT_COLUMN} TEXT NULL,
            FOREIGN KEY (doc_id) REFERENCES {DOCUMENTS_TABLE_NAME}(id) ON DELETE CASCADE,
            FOREIGN KEY (processing_id) REFERENCES {PROCESSINGS_TABLE_NAME}(id) ON DELETE CASCADE,
            CHECK(start_offset >= 0),
            CHECK(end_offset > start_offset)
        );

        CREATE TABLE {RULES_TABLE_NAME} (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL CHECK(type IN ('fvg')),
            path TEXT NOT NULL
        );

        CREATE TABLE {RULE_FVG_TABLE_NAME} (
            id TEXT PRIMARY KEY,
            rule_id TEXT NOT NULL,
            verb TEXT NOT NULL,
            phrase TEXT NOT NULL,
            FOREIGN KEY (rule_id) REFERENCES {RULES_TABLE_NAME}(id) ON DELETE CASCADE
        );

        CREATE INDEX {PROCESSINGS_DOC_TYPE_CREATED_AT_INDEX_NAME}
        ON {PROCESSINGS_TABLE_NAME} (doc_id, type, created_at);

        CREATE INDEX {DOCUMENT_SENTENCES_PROCESSING_DOC_START_OFFSET_INDEX_NAME}
        ON {DOCUMENT_SENTENCES_TABLE_NAME} (processing_id, doc_id, start_offset);

        CREATE INDEX {RULE_FVG_RULE_ID_INDEX_NAME}
        ON {RULE_FVG_TABLE_NAME} (rule_id);

        CREATE TRIGGER {DOCUMENT_SENTENCES_SOURCE_TEXT_LOCK_TRIGGER_NAME}
        BEFORE UPDATE OF {DOCUMENT_SENTENCES_SOURCE_TEXT_COLUMN}
        ON {DOCUMENT_SENTENCES_TABLE_NAME}
        FOR EACH ROW
        WHEN NEW.{DOCUMENT_SENTENCES_SOURCE_TEXT_COLUMN}
             IS NOT OLD.{DOCUMENT_SENTENCES_SOURCE_TEXT_COLUMN}
        BEGIN
            SELECT RAISE(ABORT, 'document_sentences.source_text is locked');
        END;
        """
    )
    connection.commit()


def _validate_schema(connection: Connection) -> None:
    expected_tables = set(EXPECTED_TABLE_COLUMNS)
    actual_tables = _list_user_tables(connection)
    if actual_tables != expected_tables:
        missing_tables = sorted(expected_tables - actual_tables)
        extra_tables = sorted(actual_tables - expected_tables)
        raise _schema_drift_error(
            f"tables_mismatch missing={missing_tables} extra={extra_tables}"
        )

    for table_name, expected_columns in EXPECTED_TABLE_COLUMNS.items():
        actual_columns = _table_columns(connection, table_name)
        if actual_columns != expected_columns:
            raise _schema_drift_error(
                "columns_mismatch "
                f"table={table_name} expected={list(expected_columns)} actual={list(actual_columns)}"
            )

    actual_indexes = _list_indexes(connection)
    missing_indexes = sorted(
        index_name for index_name in EXPECTED_INDEXES if index_name not in actual_indexes
    )
    if missing_indexes:
        raise _schema_drift_error(f"missing_indexes={missing_indexes}")

    actual_triggers = _list_triggers(connection)
    missing_triggers = sorted(
        trigger_name
        for trigger_name in EXPECTED_TRIGGERS
        if trigger_name not in actual_triggers
    )
    if missing_triggers:
        raise _schema_drift_error(f"missing_triggers={missing_triggers}")


def _schema_drift_error(reason: str) -> RuntimeError:
    return RuntimeError(
        "SQLite schema drift detected. "
        f"reason={reason}. 请developer先清空sqlite3: {settings.sqlite_database_path}"
    )


def _list_user_tables(connection: Connection) -> set[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {str(row["name"]) for row in rows}


def _table_columns(connection: Connection, table_name: str) -> tuple[str, ...]:
    rows = connection.execute(f'PRAGMA table_info("{table_name}")').fetchall()
    return tuple(str(row["name"]) for row in rows)


def _list_indexes(connection: Connection) -> set[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'index' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {str(row["name"]) for row in rows}


def _list_triggers(connection: Connection) -> set[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'trigger'"
    ).fetchall()
    return {str(row["name"]) for row in rows}
