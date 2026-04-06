from datetime import datetime, timezone
from sqlite3 import Connection

from app.core.config import settings
from app.core.log import get_logger, log_event
from app.infrastructure.db.connection import connection_scope
from app.infrastructure.db.schema import (
    DOCUMENTS_TABLE_NAME,
    FVG_CANDIDATES_TABLE_NAME,
    FVG_ENTRIES_TABLE_NAME,
    LEMMA_TOKENS_TABLE_NAME,
    PROCESSINGS_TABLE_NAME,
    RULES_TABLE_NAME,
    SENTENCES_TABLE_NAME,
)

LOGGER = get_logger(__name__)
MODULE_FILE = __file__

OLD_SENTENCES_TABLE_NAME = "document_sentences"
OLD_LEMMA_TABLE_NAME = "lemma"
OLD_FVG_TABLE_NAME = "rule_fvg"


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
    else:
        _apply_migrations_with_connection(connection)

    log_event(
        LOGGER,
        stage="OK",
        module_file=MODULE_FILE,
        function_name=function_name,
        result="migrations_applied",
    )


def _apply_migrations_with_connection(connection: Connection) -> None:
    function_name = "_apply_migrations_with_connection"

    _migrate_documents_char_count(connection)
    _migrate_processings_parent_id(connection)
    _migrate_sentences_table(connection)
    _migrate_lemma_tokens_table(connection)
    _migrate_rules_table(connection)
    _migrate_fvg_entries_table(connection)
    _migrate_fvg_candidates_table(connection)

    connection.commit()

    log_event(
        LOGGER,
        stage="OK",
        module_file=MODULE_FILE,
        function_name=function_name,
        result="schema_compat_ready",
    )


def _table_exists(connection: Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ? LIMIT 1",
        (table_name,),
    ).fetchone()
    return row is not None


def _column_exists(connection: Connection, table_name: str, column_name: str) -> bool:
    if not _table_exists(connection, table_name):
        return False

    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(str(row["name"]) == column_name for row in rows)


def _migrate_documents_char_count(connection: Connection) -> None:
    if not _table_exists(connection, DOCUMENTS_TABLE_NAME):
        return

    if not _column_exists(connection, DOCUMENTS_TABLE_NAME, "char_count"):
        connection.execute(
            f"ALTER TABLE {DOCUMENTS_TABLE_NAME} ADD COLUMN char_count INTEGER NOT NULL DEFAULT 0"
        )

    if _column_exists(connection, DOCUMENTS_TABLE_NAME, "text_char_count"):
        connection.execute(
            f"""
            UPDATE {DOCUMENTS_TABLE_NAME}
            SET char_count = text_char_count
            WHERE char_count = 0
            """
        )


def _migrate_processings_parent_id(connection: Connection) -> None:
    if not _table_exists(connection, PROCESSINGS_TABLE_NAME):
        return

    if not _column_exists(connection, PROCESSINGS_TABLE_NAME, "parent_id"):
        connection.execute(
            f"ALTER TABLE {PROCESSINGS_TABLE_NAME} ADD COLUMN parent_id TEXT"
        )

    connection.execute(
        f"""
        UPDATE {PROCESSINGS_TABLE_NAME}
        SET parent_id = id
        WHERE parent_id IS NULL OR TRIM(parent_id) = ''
        """
    )


def _migrate_sentences_table(connection: Connection) -> None:
    if _table_exists(connection, OLD_SENTENCES_TABLE_NAME) and not _table_exists(connection, SENTENCES_TABLE_NAME):
        connection.execute(
            f"""
            CREATE TABLE {SENTENCES_TABLE_NAME} (
                id TEXT PRIMARY KEY,
                version_id TEXT NOT NULL,
                doc_id TEXT NOT NULL,
                start_offset INTEGER NOT NULL,
                end_offset INTEGER NOT NULL,
                source_text TEXT NOT NULL,
                corrected_text TEXT NOT NULL,
                FOREIGN KEY (version_id) REFERENCES {PROCESSINGS_TABLE_NAME}(id) ON DELETE CASCADE,
                FOREIGN KEY (doc_id) REFERENCES {DOCUMENTS_TABLE_NAME}(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            f"""
            INSERT INTO {SENTENCES_TABLE_NAME} (
                id,
                version_id,
                doc_id,
                start_offset,
                end_offset,
                source_text,
                corrected_text
            )
            SELECT
                id,
                processing_id,
                doc_id,
                start_offset,
                end_offset,
                source_text,
                source_text
            FROM {OLD_SENTENCES_TABLE_NAME}
            """
        )

    if not _table_exists(connection, SENTENCES_TABLE_NAME):
        return

    if not _column_exists(connection, SENTENCES_TABLE_NAME, "version_id") and _column_exists(connection, SENTENCES_TABLE_NAME, "processing_id"):
        connection.execute(
            f"ALTER TABLE {SENTENCES_TABLE_NAME} ADD COLUMN version_id TEXT"
        )
        connection.execute(
            f"UPDATE {SENTENCES_TABLE_NAME} SET version_id = processing_id WHERE version_id IS NULL"
        )

    if not _column_exists(connection, SENTENCES_TABLE_NAME, "corrected_text"):
        connection.execute(
            f"ALTER TABLE {SENTENCES_TABLE_NAME} ADD COLUMN corrected_text TEXT"
        )
        connection.execute(
            f"UPDATE {SENTENCES_TABLE_NAME} SET corrected_text = source_text WHERE corrected_text IS NULL"
        )


def _migrate_lemma_tokens_table(connection: Connection) -> None:
    if _table_exists(connection, LEMMA_TOKENS_TABLE_NAME):
        return

    connection.execute(
        f"""
        CREATE TABLE {LEMMA_TOKENS_TABLE_NAME} (
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
        )
        """
    )

    # Legacy sentence-level lemma rows are intentionally not copied into token-level table.
    if _table_exists(connection, OLD_LEMMA_TABLE_NAME):
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name="_migrate_lemma_tokens_table",
            result="legacy_lemma_table_detected_skip_copy",
        )


def _migrate_rules_table(connection: Connection) -> None:
    if not _table_exists(connection, RULES_TABLE_NAME):
        return

    if _column_exists(connection, RULES_TABLE_NAME, "version_id"):
        return

    connection.execute(
        f"ALTER TABLE {RULES_TABLE_NAME} ADD COLUMN version_id TEXT"
    )

    now_iso = datetime.now(timezone.utc).isoformat()
    rows = connection.execute(
        f"SELECT id FROM {RULES_TABLE_NAME}"
    ).fetchall()
    for row in rows:
        rule_id = str(row["id"])
        process_id = f"legacy_import_rule_{rule_id}"
        connection.execute(
            f"""
            INSERT OR IGNORE INTO {PROCESSINGS_TABLE_NAME} (
                id,
                parent_id,
                doc_id,
                type,
                state,
                created_at,
                updated_at,
                error_message,
                meta_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                process_id,
                process_id,
                None,
                "import_rule",
                "succeed",
                now_iso,
                now_iso,
                None,
                '{"legacy": true}',
            ),
        )
        connection.execute(
            f"UPDATE {RULES_TABLE_NAME} SET version_id = ? WHERE id = ?",
            (process_id, rule_id),
        )


def _migrate_fvg_entries_table(connection: Connection) -> None:
    if _table_exists(connection, OLD_FVG_TABLE_NAME) and not _table_exists(connection, FVG_ENTRIES_TABLE_NAME):
        connection.execute(
            f"""
            CREATE TABLE {FVG_ENTRIES_TABLE_NAME} (
                id TEXT PRIMARY KEY,
                rule_id TEXT NOT NULL,
                verb TEXT NOT NULL,
                phrase TEXT NOT NULL,
                noun TEXT NOT NULL,
                prep TEXT NOT NULL,
                structure_type TEXT NOT NULL,
                semantic_type TEXT NOT NULL,
                FOREIGN KEY (rule_id) REFERENCES {RULES_TABLE_NAME}(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            f"""
            INSERT INTO {FVG_ENTRIES_TABLE_NAME} (
                id,
                rule_id,
                verb,
                phrase,
                noun,
                prep,
                structure_type,
                semantic_type
            )
            SELECT
                id,
                rule_id,
                verb,
                phrase,
                '',
                '',
                'prep',
                'unknown'
            FROM {OLD_FVG_TABLE_NAME}
            """
        )

    if not _table_exists(connection, FVG_ENTRIES_TABLE_NAME):
        return

    for column_name, definition in (
        ("noun", "TEXT NOT NULL DEFAULT ''"),
        ("prep", "TEXT NOT NULL DEFAULT ''"),
        ("structure_type", "TEXT NOT NULL DEFAULT 'prep'"),
        ("semantic_type", "TEXT NOT NULL DEFAULT 'unknown'"),
    ):
        if not _column_exists(connection, FVG_ENTRIES_TABLE_NAME, column_name):
            connection.execute(
                f"ALTER TABLE {FVG_ENTRIES_TABLE_NAME} ADD COLUMN {column_name} {definition}"
            )


def _migrate_fvg_candidates_table(connection: Connection) -> None:
    if not _table_exists(connection, FVG_CANDIDATES_TABLE_NAME):
        connection.execute(
            f"""
            CREATE TABLE {FVG_CANDIDATES_TABLE_NAME} (
                id TEXT PRIMARY KEY,
                sentence_id TEXT NOT NULL,
                process_id TEXT NOT NULL DEFAULT '',
                algo_fvg_entry_id TEXT NOT NULL DEFAULT '',
                corrected_fvg_entry_id TEXT NOT NULL DEFAULT '',
                algo_verb_token TEXT NOT NULL DEFAULT '',
                algo_verb_index INTEGER NOT NULL DEFAULT -1,
                corrected_verb_token TEXT NOT NULL DEFAULT '',
                corrected_verb_index INTEGER NOT NULL DEFAULT -1,
                algo_noun_token TEXT NOT NULL DEFAULT '',
                algo_noun_index INTEGER NOT NULL DEFAULT -1,
                corrected_noun_token TEXT NOT NULL DEFAULT '',
                corrected_noun_index INTEGER NOT NULL DEFAULT -1,
                algo_prep_token TEXT NOT NULL DEFAULT '',
                algo_prep_index INTEGER NOT NULL DEFAULT -1,
                corrected_prep_token TEXT NOT NULL DEFAULT '',
                corrected_prep_index INTEGER NOT NULL DEFAULT -1,
                label TEXT NOT NULL DEFAULT '',
                manuelle_created INTEGER NOT NULL DEFAULT 0,
                removed INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (sentence_id) REFERENCES {SENTENCES_TABLE_NAME}(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_fvg_candidates_sentence_id
            ON {FVG_CANDIDATES_TABLE_NAME} (sentence_id)
            """
        )
        return

    for column_name, definition in (
        ("process_id", "TEXT NOT NULL DEFAULT ''"),
        ("algo_fvg_entry_id", "TEXT NOT NULL DEFAULT ''"),
        ("corrected_fvg_entry_id", "TEXT NOT NULL DEFAULT ''"),
        ("algo_verb_token", "TEXT NOT NULL DEFAULT ''"),
        ("algo_verb_index", "INTEGER NOT NULL DEFAULT -1"),
        ("corrected_verb_token", "TEXT NOT NULL DEFAULT ''"),
        ("corrected_verb_index", "INTEGER NOT NULL DEFAULT -1"),
        ("algo_noun_token", "TEXT NOT NULL DEFAULT ''"),
        ("algo_noun_index", "INTEGER NOT NULL DEFAULT -1"),
        ("corrected_noun_token", "TEXT NOT NULL DEFAULT ''"),
        ("corrected_noun_index", "INTEGER NOT NULL DEFAULT -1"),
        ("algo_prep_token", "TEXT NOT NULL DEFAULT ''"),
        ("algo_prep_index", "INTEGER NOT NULL DEFAULT -1"),
        ("corrected_prep_token", "TEXT NOT NULL DEFAULT ''"),
        ("corrected_prep_index", "INTEGER NOT NULL DEFAULT -1"),
        ("label", "TEXT NOT NULL DEFAULT ''"),
        ("manuelle_created", "INTEGER NOT NULL DEFAULT 0"),
        ("removed", "INTEGER NOT NULL DEFAULT 0"),
    ):
        if not _column_exists(connection, FVG_CANDIDATES_TABLE_NAME, column_name):
            connection.execute(
                f"ALTER TABLE {FVG_CANDIDATES_TABLE_NAME} ADD COLUMN {column_name} {definition}"
            )

    # keep corrected string fields normalized to empty string by default
    connection.execute(
        f"""
        UPDATE {FVG_CANDIDATES_TABLE_NAME}
        SET corrected_fvg_entry_id = COALESCE(corrected_fvg_entry_id, ''),
            corrected_verb_token = COALESCE(corrected_verb_token, ''),
            corrected_verb_index = COALESCE(corrected_verb_index, -1),
            corrected_noun_token = COALESCE(corrected_noun_token, ''),
            corrected_noun_index = COALESCE(corrected_noun_index, -1),
            corrected_prep_token = COALESCE(corrected_prep_token, ''),
            corrected_prep_index = COALESCE(corrected_prep_index, -1),
            process_id = COALESCE(process_id, '')
        """
    )

    connection.execute(
        f"""
        CREATE INDEX IF NOT EXISTS idx_fvg_candidates_sentence_id
        ON {FVG_CANDIDATES_TABLE_NAME} (sentence_id)
        """
    )


__all__ = ["apply_migrations"]
