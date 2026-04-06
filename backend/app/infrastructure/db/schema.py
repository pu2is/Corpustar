from sqlite3 import Connection

from app.core.config import settings
from app.core.log import get_logger, log_event
from app.infrastructure.db.connection import connection_scope

DOCUMENTS_TABLE_NAME = "documents"
PROCESSINGS_TABLE_NAME = "processings"
SENTENCES_TABLE_NAME = "sentences"
LEMMA_TOKENS_TABLE_NAME = "lemma_tokens"
RULES_TABLE_NAME = "rules"
FVG_ENTRIES_TABLE_NAME = "fvg_entries"
FVG_CANDIDATES_TABLE_NAME = "fvg_candidates"

PROCESSINGS_DOC_TYPE_CREATED_AT_INDEX_NAME = "idx_processings_doc_type_created_at"
SENTENCES_VERSION_DOC_START_OFFSET_INDEX_NAME = "idx_sentences_version_doc_start_offset"
LEMMA_TOKENS_VERSION_SENTENCE_WORD_INDEX_NAME = "idx_lemma_tokens_version_sentence_word"
FVG_ENTRIES_RULE_ID_INDEX_NAME = "idx_fvg_entries_rule_id"
FVG_CANDIDATES_SENTENCE_ID_INDEX_NAME = "idx_fvg_candidates_sentence_id"
SENTENCES_SOURCE_TEXT_LOCK_TRIGGER_NAME = "trg_sentences_source_text_locked"

REQUIRED_TABLES = {
    DOCUMENTS_TABLE_NAME,
    PROCESSINGS_TABLE_NAME,
    SENTENCES_TABLE_NAME,
    LEMMA_TOKENS_TABLE_NAME,
    RULES_TABLE_NAME,
    FVG_ENTRIES_TABLE_NAME,
    FVG_CANDIDATES_TABLE_NAME,
}
REQUIRED_INDEXES = {
    PROCESSINGS_DOC_TYPE_CREATED_AT_INDEX_NAME,
    SENTENCES_VERSION_DOC_START_OFFSET_INDEX_NAME,
    LEMMA_TOKENS_VERSION_SENTENCE_WORD_INDEX_NAME,
    FVG_ENTRIES_RULE_ID_INDEX_NAME,
    FVG_CANDIDATES_SENTENCE_ID_INDEX_NAME,
}
REQUIRED_TRIGGERS = {
    SENTENCES_SOURCE_TEXT_LOCK_TRIGGER_NAME,
}

SCHEMA_SQL = f"""
CREATE TABLE IF NOT EXISTS {DOCUMENTS_TABLE_NAME} (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    display_name TEXT NOT NULL,
    note TEXT NOT NULL,
    source_path TEXT NOT NULL,
    text_path TEXT NOT NULL,
    char_count INTEGER NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS {PROCESSINGS_TABLE_NAME} (
    id TEXT PRIMARY KEY,
    parent_id TEXT NOT NULL,
    doc_id TEXT NULL,
    type TEXT NOT NULL CHECK(type IN ('sentence_segmentation', 'lemma', 'fvg', 'import_rule')),
    state TEXT NOT NULL CHECK(state IN ('running', 'succeed', 'failed')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    error_message TEXT NULL,
    meta_json TEXT NULL,
    FOREIGN KEY (doc_id) REFERENCES {DOCUMENTS_TABLE_NAME}(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS {SENTENCES_TABLE_NAME} (
    id TEXT PRIMARY KEY,
    version_id TEXT NOT NULL,
    doc_id TEXT NOT NULL,
    start_offset INTEGER NOT NULL,
    end_offset INTEGER NOT NULL,
    source_text TEXT NOT NULL,
    corrected_text TEXT NOT NULL,
    FOREIGN KEY (version_id) REFERENCES {PROCESSINGS_TABLE_NAME}(id) ON DELETE CASCADE,
    FOREIGN KEY (doc_id) REFERENCES {DOCUMENTS_TABLE_NAME}(id) ON DELETE CASCADE,
    CHECK(start_offset >= 0),
    CHECK(end_offset > start_offset)
);

CREATE TABLE IF NOT EXISTS {LEMMA_TOKENS_TABLE_NAME} (
    id TEXT PRIMARY KEY,
    version_id TEXT NOT NULL,
    sentence_id TEXT NOT NULL,
    source_word TEXT NOT NULL,
    lemma_word TEXT NOT NULL,
    word_index INTEGER NOT NULL,
    head_index INTEGER NOT NULL,
    pos_tag TEXT NOT NULL,
    fine_pos_tag TEXT NOT NULL,
    morph TEXT NOT NULL,
    dependency_relationship TEXT NOT NULL,
    FOREIGN KEY (version_id) REFERENCES {PROCESSINGS_TABLE_NAME}(id) ON DELETE CASCADE,
    FOREIGN KEY (sentence_id) REFERENCES {SENTENCES_TABLE_NAME}(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS {RULES_TABLE_NAME} (
    id TEXT PRIMARY KEY,
    version_id TEXT NOT NULL,
    type TEXT NOT NULL,
    path TEXT NOT NULL,
    FOREIGN KEY (version_id) REFERENCES {PROCESSINGS_TABLE_NAME}(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS {FVG_ENTRIES_TABLE_NAME} (
    id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    verb TEXT NOT NULL,
    phrase TEXT NOT NULL,
    noun TEXT NOT NULL,
    prep TEXT NOT NULL,
    structure_type TEXT NOT NULL CHECK(structure_type IN ('prep', 'akku')),
    semantic_type TEXT NOT NULL,
    FOREIGN KEY (rule_id) REFERENCES {RULES_TABLE_NAME}(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS {FVG_CANDIDATES_TABLE_NAME} (
    id TEXT PRIMARY KEY,
    sentence_id TEXT NOT NULL,
    process_id TEXT NOT NULL DEFAULT '',
    algo_fvg_entry_id TEXT NOT NULL,
    corrected_fvg_entry_id TEXT NOT NULL DEFAULT '',
    algo_verb_token TEXT NOT NULL,
    algo_verb_index INTEGER NOT NULL,
    corrected_verb_token TEXT NOT NULL DEFAULT '',
    corrected_verb_index INTEGER NOT NULL DEFAULT -1,
    algo_noun_token TEXT NOT NULL,
    algo_noun_index INTEGER NOT NULL,
    corrected_noun_token TEXT NOT NULL DEFAULT '',
    corrected_noun_index INTEGER NOT NULL DEFAULT -1,
    algo_prep_token TEXT NOT NULL,
    algo_prep_index INTEGER NOT NULL,
    corrected_prep_token TEXT NOT NULL DEFAULT '',
    corrected_prep_index INTEGER NOT NULL DEFAULT -1,
    label TEXT NOT NULL CHECK(label IN ('', 'TP', 'FP', 'FN')),
    manuelle_created INTEGER NOT NULL DEFAULT 0 CHECK(manuelle_created IN (0, 1)),
    removed INTEGER NOT NULL DEFAULT 0 CHECK(removed IN (0, 1)),
    FOREIGN KEY (sentence_id) REFERENCES {SENTENCES_TABLE_NAME}(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS {PROCESSINGS_DOC_TYPE_CREATED_AT_INDEX_NAME}
ON {PROCESSINGS_TABLE_NAME} (doc_id, type, created_at);

CREATE INDEX IF NOT EXISTS {SENTENCES_VERSION_DOC_START_OFFSET_INDEX_NAME}
ON {SENTENCES_TABLE_NAME} (version_id, doc_id, start_offset);

CREATE INDEX IF NOT EXISTS {LEMMA_TOKENS_VERSION_SENTENCE_WORD_INDEX_NAME}
ON {LEMMA_TOKENS_TABLE_NAME} (version_id, sentence_id, word_index);

CREATE INDEX IF NOT EXISTS {FVG_ENTRIES_RULE_ID_INDEX_NAME}
ON {FVG_ENTRIES_TABLE_NAME} (rule_id);

CREATE INDEX IF NOT EXISTS {FVG_CANDIDATES_SENTENCE_ID_INDEX_NAME}
ON {FVG_CANDIDATES_TABLE_NAME} (sentence_id);

CREATE TRIGGER IF NOT EXISTS {SENTENCES_SOURCE_TEXT_LOCK_TRIGGER_NAME}
BEFORE UPDATE OF source_text
ON {SENTENCES_TABLE_NAME}
FOR EACH ROW
WHEN NEW.source_text IS NOT OLD.source_text
BEGIN
    SELECT RAISE(ABORT, 'sentences.source_text is locked');
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
    connection.executescript(SCHEMA_SQL)
    connection.commit()
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
