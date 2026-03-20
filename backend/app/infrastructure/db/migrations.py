from sqlite3 import Connection

from app.core.config import settings
from app.core.log import get_logger, log_event
from app.infrastructure.db.connection import connection_scope
from app.infrastructure.db.schema import (
    DOCUMENT_SENTENCES_TABLE_NAME,
    DOCUMENTS_TABLE_NAME,
    LEMMA_SEGMENTATION_SENTENCE_INDEX_NAME,
    LEMMA_TABLE_NAME,
    PROCESSINGS_TABLE_NAME,
)

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
    function_name = "_apply_migrations_with_connection"
    table_names = {
        str(row["name"])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    }

    if DOCUMENT_SENTENCES_TABLE_NAME in table_names and LEMMA_TABLE_NAME not in table_names:
        connection.executescript(
            f"""
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

            CREATE INDEX {LEMMA_SEGMENTATION_SENTENCE_INDEX_NAME}
            ON {LEMMA_TABLE_NAME} (segmentation_id, sentence_id);
            """
        )
        connection.commit()

    log_event(
        LOGGER,
        stage="OK",
        module_file=MODULE_FILE,
        function_name=function_name,
        result="lemma_schema_checked",
    )
    log_event(
        LOGGER,
        stage="OK",
        module_file=MODULE_FILE,
        function_name="apply_migrations",
        result="migrations_applied",
    )


__all__ = ["apply_migrations"]
