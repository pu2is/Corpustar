from collections.abc import Generator, Iterable, Mapping
from contextlib import contextmanager
from sqlite3 import Connection

from sqlalchemy import bindparam, delete, insert, select, update

from app.infrastructure.db.connection import connection_scope
from app.infrastructure.repositories._sqlalchemy import (
    execute,
    execute_many,
    fvg_entries_table,
)

FvgEntryRow = dict[str, str]


def _map_fvg_entry_row(row: Mapping[str, object]) -> FvgEntryRow:
    return {
        "id": str(row["id"]),
        "rule_id": str(row["rule_id"]),
        "verb": str(row["verb"]),
        "phrase": str(row["phrase"]),
        "noun": str(row["noun"]),
        "prep": str(row["prep"]),
        "structure_type": str(row["structure_type"]),
        "semantic_type": str(row["semantic_type"]),
    }


@contextmanager
def _use_connection(connection: Connection | None) -> Generator[Connection, None, None]:
    if connection is not None:
        yield connection
        return

    with connection_scope() as scoped_connection:
        yield scoped_connection


def save_fvg_entries_in_batch(
    rows: Iterable[Mapping[str, str]],
    connection: Connection | None = None,
) -> list[FvgEntryRow]:
    normalized_rows = [_normalize_fvg_entry_row(row) for row in rows]
    if not normalized_rows:
        return []

    statement = insert(fvg_entries_table).values(
        id=bindparam("id"),
        rule_id=bindparam("rule_id"),
        verb=bindparam("verb"),
        phrase=bindparam("phrase"),
        noun=bindparam("noun"),
        prep=bindparam("prep"),
        structure_type=bindparam("structure_type"),
        semantic_type=bindparam("semantic_type"),
    )

    owns_connection = connection is None
    with _use_connection(connection) as active_connection:
        try:
            execute_many(active_connection, statement, normalized_rows)
            if owns_connection:
                active_connection.commit()
            return normalized_rows
        except Exception:
            if owns_connection:
                active_connection.rollback()
            raise


def write_fvg_entry_item(
    row: Mapping[str, str],
    connection: Connection | None = None,
) -> FvgEntryRow:
    inserted_row = _normalize_fvg_entry_row(row)

    owns_connection = connection is None
    with _use_connection(connection) as active_connection:
        try:
            execute(active_connection, insert(fvg_entries_table).values(**inserted_row))
            if owns_connection:
                active_connection.commit()
            return inserted_row
        except Exception:
            if owns_connection:
                active_connection.rollback()
            raise


def get_fvg_entry_by_id(
    fvg_id: str,
    connection: Connection | None = None,
) -> FvgEntryRow | None:
    statement = (
        select(
            fvg_entries_table.c.id,
            fvg_entries_table.c.rule_id,
            fvg_entries_table.c.verb,
            fvg_entries_table.c.phrase,
            fvg_entries_table.c.noun,
            fvg_entries_table.c.prep,
            fvg_entries_table.c.structure_type,
            fvg_entries_table.c.semantic_type,
        )
        .select_from(fvg_entries_table)
        .where(fvg_entries_table.c.id == fvg_id)
    )
    with _use_connection(connection) as active_connection:
        row = execute(active_connection, statement).fetchone()

    if row is None:
        return None
    return _map_fvg_entry_row(row)


def get_fvg_entries_by_rule_id(
    rule_id: str,
    connection: Connection | None = None,
) -> list[FvgEntryRow]:
    statement = (
        select(
            fvg_entries_table.c.id,
            fvg_entries_table.c.rule_id,
            fvg_entries_table.c.verb,
            fvg_entries_table.c.phrase,
            fvg_entries_table.c.noun,
            fvg_entries_table.c.prep,
            fvg_entries_table.c.structure_type,
            fvg_entries_table.c.semantic_type,
        )
        .select_from(fvg_entries_table)
        .where(fvg_entries_table.c.rule_id == rule_id)
        .order_by(fvg_entries_table.c.id.asc())
    )
    with _use_connection(connection) as active_connection:
        rows = execute(active_connection, statement).fetchall()

    return [_map_fvg_entry_row(row) for row in rows]


def modify_fvg_by_id(
    fvg_id: str,
    *,
    verb: str | None = None,
    phrase: str | None = None,
    noun: str | None = None,
    prep: str | None = None,
    structure_type: str | None = None,
    semantic_type: str | None = None,
    connection: Connection | None = None,
) -> FvgEntryRow:
    values_to_update: dict[str, str] = {}
    for column_name, value in (
        ("verb", verb),
        ("phrase", phrase),
        ("noun", noun),
        ("prep", prep),
        ("structure_type", structure_type),
        ("semantic_type", semantic_type),
    ):
        if value is not None:
            values_to_update[column_name] = value

    if not values_to_update:
        existing = get_fvg_entry_by_id(fvg_id=fvg_id, connection=connection)
        if existing is None:
            raise FileNotFoundError(f"FVG entry not found: {fvg_id}")
        return existing

    owns_connection = connection is None
    with _use_connection(connection) as active_connection:
        try:
            cursor = execute(
                active_connection,
                update(fvg_entries_table)
                .where(fvg_entries_table.c.id == fvg_id)
                .values(**values_to_update),
            )
            if cursor.rowcount <= 0:
                raise FileNotFoundError(f"FVG entry not found: {fvg_id}")

            row = get_fvg_entry_by_id(fvg_id=fvg_id, connection=active_connection)
            if row is None:
                raise FileNotFoundError(f"FVG entry not found after update: {fvg_id}")

            if owns_connection:
                active_connection.commit()
            return row
        except Exception:
            if owns_connection:
                active_connection.rollback()
            raise


def rm_fvg_entry_by_id(
    fvg_id: str,
    connection: Connection | None = None,
) -> bool:
    owns_connection = connection is None
    with _use_connection(connection) as active_connection:
        try:
            cursor = execute(
                active_connection,
                delete(fvg_entries_table).where(fvg_entries_table.c.id == fvg_id),
            )
            if owns_connection:
                active_connection.commit()
            return cursor.rowcount > 0
        except Exception:
            if owns_connection:
                active_connection.rollback()
            raise


def filter_fvg_entry_by_rule_and_verb(
    rule_id: str,
    verb: str,
    connection: Connection | None = None,
) -> list[FvgEntryRow]:
    statement = (
        select(
            fvg_entries_table.c.id,
            fvg_entries_table.c.rule_id,
            fvg_entries_table.c.verb,
            fvg_entries_table.c.phrase,
            fvg_entries_table.c.noun,
            fvg_entries_table.c.prep,
            fvg_entries_table.c.structure_type,
            fvg_entries_table.c.semantic_type,
        )
        .select_from(fvg_entries_table)
        .where(
            fvg_entries_table.c.rule_id == rule_id,
            fvg_entries_table.c.verb == verb,
        )
        .order_by(fvg_entries_table.c.id.asc())
    )
    with _use_connection(connection) as active_connection:
        rows = execute(active_connection, statement).fetchall()

    return [_map_fvg_entry_row(row) for row in rows]


def rm_fvg_entries_by_rule_id(
    rule_id: str,
    connection: Connection | None = None,
) -> int:
    owns_connection = connection is None
    with _use_connection(connection) as active_connection:
        try:
            cursor = execute(
                active_connection,
                delete(fvg_entries_table).where(fvg_entries_table.c.rule_id == rule_id),
            )
            if owns_connection:
                active_connection.commit()
            return cursor.rowcount
        except Exception:
            if owns_connection:
                active_connection.rollback()
            raise


def _normalize_fvg_entry_row(row: Mapping[str, str]) -> FvgEntryRow:
    return {
        "id": str(row["id"]),
        "rule_id": str(row["rule_id"]),
        "verb": str(row["verb"]),
        "phrase": str(row["phrase"]),
        "noun": str(row["noun"]),
        "prep": str(row["prep"]),
        "structure_type": str(row["structure_type"]),
        "semantic_type": str(row["semantic_type"]),
    }
