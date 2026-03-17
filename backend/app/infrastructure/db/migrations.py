from collections.abc import Callable
from sqlite3 import Connection

from app.core.config import settings
from app.core.log import get_logger, log_event
from app.infrastructure.db.connection import connection_scope
from app.infrastructure.db.schema import (
    DOCUMENT_SENTENCES_TABLE_NAME,
    DOCUMENTS_TABLE_NAME,
    DOCUMENTS_TEXT_CHAR_COUNT_COLUMN,
    PROCESSINGS_TABLE_NAME,
)

LOGGER = get_logger(__name__)
MODULE_FILE = __file__
MigrationStep = tuple[str, Callable[[Connection], None]]


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
    try:
        for migration_name, migration_step in _ordered_migration_steps():
            log_event(
                LOGGER,
                stage="CALL",
                module_file=MODULE_FILE,
                function_name=function_name,
                migration_name=migration_name,
            )
            migration_step(connection)
            log_event(
                LOGGER,
                stage="OK",
                module_file=MODULE_FILE,
                function_name=function_name,
                migration_name=migration_name,
                result="applied_or_skipped",
            )
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name="apply_migrations",
            result="migrations_applied",
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


def _ordered_migration_steps() -> tuple[MigrationStep, ...]:
    # Keep migrations in deterministic order. Append new versioned steps here.
    return (
        (
            "20260317_add_documents_text_char_count",
            _ensure_documents_text_char_count_column,
        ),
        (
            "20260317_verify_legacy_cascade_foreign_keys",
            _ensure_legacy_foreign_key_compatibility,
        ),
    )


def _ensure_documents_text_char_count_column(connection: Connection) -> None:
    function_name = "_ensure_documents_text_char_count_column"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        table_name=DOCUMENTS_TABLE_NAME,
        column_name=DOCUMENTS_TEXT_CHAR_COUNT_COLUMN,
    )
    if not _table_exists(connection, DOCUMENTS_TABLE_NAME):
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            result="table_missing_skip",
        )
        return

    if _column_exists(
        connection,
        DOCUMENTS_TABLE_NAME,
        DOCUMENTS_TEXT_CHAR_COUNT_COLUMN,
    ):
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            result="column_already_exists",
        )
        return

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
        result="column_added",
    )


def _ensure_legacy_foreign_key_compatibility(connection: Connection) -> None:
    function_name = "_ensure_legacy_foreign_key_compatibility"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
    )

    required_tables = (
        DOCUMENTS_TABLE_NAME,
        PROCESSINGS_TABLE_NAME,
        DOCUMENT_SENTENCES_TABLE_NAME,
    )
    missing_tables = [table_name for table_name in required_tables if not _table_exists(connection, table_name)]
    if missing_tables:
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            missing_tables=",".join(missing_tables),
            result="tables_missing_skip",
        )
        return

    missing_constraints: list[str] = []

    if not _foreign_key_exists(
        connection=connection,
        table_name=PROCESSINGS_TABLE_NAME,
        from_column="doc_id",
        referenced_table=DOCUMENTS_TABLE_NAME,
        referenced_column="id",
        on_delete="CASCADE",
    ):
        missing_constraints.append(
            f"{PROCESSINGS_TABLE_NAME}.doc_id -> {DOCUMENTS_TABLE_NAME}.id ON DELETE CASCADE"
        )

    if not _foreign_key_exists(
        connection=connection,
        table_name=DOCUMENT_SENTENCES_TABLE_NAME,
        from_column="doc_id",
        referenced_table=DOCUMENTS_TABLE_NAME,
        referenced_column="id",
        on_delete="CASCADE",
    ):
        missing_constraints.append(
            f"{DOCUMENT_SENTENCES_TABLE_NAME}.doc_id -> {DOCUMENTS_TABLE_NAME}.id ON DELETE CASCADE"
        )

    if not _foreign_key_exists(
        connection=connection,
        table_name=DOCUMENT_SENTENCES_TABLE_NAME,
        from_column="processing_id",
        referenced_table=PROCESSINGS_TABLE_NAME,
        referenced_column="id",
        on_delete="CASCADE",
    ):
        missing_constraints.append(
            f"{DOCUMENT_SENTENCES_TABLE_NAME}.processing_id -> {PROCESSINGS_TABLE_NAME}.id ON DELETE CASCADE"
        )

    if missing_constraints:
        missing_details = "; ".join(missing_constraints)
        raise RuntimeError(
            "Detected legacy sqlite schema without required cascading foreign keys "
            f"({missing_details}). Rebuild local database file at "
            f"{settings.sqlite_database_path} and restart backend."
        )

    log_event(
        LOGGER,
        stage="OK",
        module_file=MODULE_FILE,
        function_name=function_name,
        result="cascade_constraints_verified",
    )


def _foreign_key_exists(
    connection: Connection,
    table_name: str,
    from_column: str,
    referenced_table: str,
    referenced_column: str,
    on_delete: str,
) -> bool:
    rows = connection.execute(f'PRAGMA foreign_key_list("{table_name}")').fetchall()
    target_on_delete = on_delete.upper()
    return any(
        str(row["from"]) == from_column
        and str(row["table"]) == referenced_table
        and str(row["to"]) == referenced_column
        and str(row["on_delete"]).upper() == target_on_delete
        for row in rows
    )


def _table_exists(connection: Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _column_exists(connection: Connection, table_name: str, column_name: str) -> bool:
    rows = connection.execute(f'PRAGMA table_info("{table_name}")').fetchall()
    return any(row["name"] == column_name for row in rows)


__all__ = ["apply_migrations"]
