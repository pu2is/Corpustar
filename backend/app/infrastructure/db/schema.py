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
LEMMA_TABLE_NAME = "lemma"
RULES_TABLE_NAME = "rules"
RULE_FVG_TABLE_NAME = "rule_fvg"

PROCESSINGS_DOC_TYPE_CREATED_AT_INDEX_NAME = "idx_processings_doc_type_created_at"
DOCUMENT_SENTENCES_PROCESSING_DOC_START_OFFSET_INDEX_NAME = (
    "idx_document_sentences_processing_doc_start_offset"
)
LEMMA_SEGMENTATION_SENTENCE_INDEX_NAME = "idx_lemma_segmentation_sentence"
RULE_FVG_RULE_ID_INDEX_NAME = "idx_rule_fvg_rule_id"
DOCUMENT_SENTENCES_SOURCE_TEXT_LOCK_TRIGGER_NAME = (
    "trg_document_sentences_source_text_locked"
)

REQUIRED_TABLES = {
    DOCUMENTS_TABLE_NAME,
    PROCESSINGS_TABLE_NAME,
    DOCUMENT_SENTENCES_TABLE_NAME,
    LEMMA_TABLE_NAME,
    RULES_TABLE_NAME,
    RULE_FVG_TABLE_NAME,
}
REQUIRED_INDEXES = {
    PROCESSINGS_DOC_TYPE_CREATED_AT_INDEX_NAME,
    DOCUMENT_SENTENCES_PROCESSING_DOC_START_OFFSET_INDEX_NAME,
    LEMMA_SEGMENTATION_SENTENCE_INDEX_NAME,
    RULE_FVG_RULE_ID_INDEX_NAME,
}
REQUIRED_TRIGGERS = {
    DOCUMENT_SENTENCES_SOURCE_TEXT_LOCK_TRIGGER_NAME,
}

SCHEMA_SQL = f"""
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

CREATE TABLE {LEMMA_TABLE_NAME} (
    id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    segmentation_id TEXT NOT NULL,
    sentence_id TEXT NOT NULL,
    source_text TEXT NOT NULL,
    lemma_text TEXT NOT NULL,
    corrected_lemma TEXT NOT NULL,
    fvg_result_id TEXT NULL,
    FOREIGN KEY (doc_id) REFERENCES {DOCUMENTS_TABLE_NAME}(id) ON DELETE CASCADE,
    FOREIGN KEY (segmentation_id) REFERENCES {PROCESSINGS_TABLE_NAME}(id) ON DELETE CASCADE,
    FOREIGN KEY (sentence_id) REFERENCES {DOCUMENT_SENTENCES_TABLE_NAME}(id) ON DELETE CASCADE
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

CREATE INDEX {LEMMA_SEGMENTATION_SENTENCE_INDEX_NAME}
ON {LEMMA_TABLE_NAME} (segmentation_id, sentence_id);

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

    try:
        if connection is None:
            settings.sqlite_database_path.parent.mkdir(parents=True, exist_ok=True)
            with connection_scope() as scoped_connection:
                _init_schema_with_connection(scoped_connection)
        else:
            _init_schema_with_connection(connection)

        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            result="ready",
        )
    except SystemExit:
        raise
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            error=str(error),
            exc_info=True,
        )
        raise SystemExit(1) from error


def _init_schema_with_connection(connection: Connection) -> None:
    if not _list_user_tables(connection):
        connection.executescript(SCHEMA_SQL)
        connection.commit()
        return

    _ensure_required_objects(connection)


def _ensure_required_objects(connection: Connection) -> None:
    table_names = _list_user_tables(connection)
    index_names = _list_object_names(connection, object_type="index", exclude_sqlite_objects=True)
    trigger_names = _list_object_names(connection, object_type="trigger")

    missing_tables = sorted(REQUIRED_TABLES - table_names)
    missing_indexes = sorted(REQUIRED_INDEXES - index_names)
    missing_triggers = sorted(REQUIRED_TRIGGERS - trigger_names)
    if not missing_tables and not missing_indexes and not missing_triggers:
        return

    raise RuntimeError(
        "SQLite schema check failed. "
        f"missing_tables={missing_tables} "
        f"missing_indexes={missing_indexes} "
        f"missing_triggers={missing_triggers} "
        f"database={settings.sqlite_database_path}"
    )


def _list_user_tables(connection: Connection) -> set[str]:
    return _list_object_names(connection, object_type="table", exclude_sqlite_objects=True)


def _list_object_names(
    connection: Connection,
    *,
    object_type: str,
    exclude_sqlite_objects: bool = False,
) -> set[str]:
    sql = "SELECT name FROM sqlite_master WHERE type = ?"
    parameters: list[str] = [object_type]
    if exclude_sqlite_objects:
        sql += " AND name NOT LIKE 'sqlite_%'"

    rows = connection.execute(sql, tuple(parameters)).fetchall()
    return {str(row["name"]) for row in rows}
