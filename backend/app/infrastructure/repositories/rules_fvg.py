from collections.abc import Generator, Iterable, Mapping
from contextlib import contextmanager
from sqlite3 import Connection, Row

from app.infrastructure.db.connection import connection_scope

RULE_FVG_TABLE_NAME = "rule_fvg"

RuleFvgRow = dict[str, str]


def _map_rule_fvg_row(row: Row) -> RuleFvgRow:
    return {
        "id": row["id"],
        "rule_id": row["rule_id"],
        "verb": row["verb"],
        "phrase": row["phrase"],
    }


@contextmanager
def _use_connection(connection: Connection | None) -> Generator[Connection, None, None]:
    if connection is not None:
        yield connection
        return

    with connection_scope() as scoped_connection:
        yield scoped_connection


def bulk_insert_rule_fvg_rows(
    rows: Iterable[Mapping[str, str]],
    connection: Connection | None = None,
) -> list[RuleFvgRow]:
    normalized_rows: list[RuleFvgRow] = [
        {
            "id": row["id"],
            "rule_id": row["rule_id"],
            "verb": row["verb"],
            "phrase": row["phrase"],
        }
        for row in rows
    ]
    if not normalized_rows:
        return []

    owns_connection = connection is None
    with _use_connection(connection) as active_connection:
        try:
            active_connection.executemany(
                f"""
                INSERT INTO {RULE_FVG_TABLE_NAME} (
                    id,
                    rule_id,
                    verb,
                    phrase
                ) VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        row["id"],
                        row["rule_id"],
                        row["verb"],
                        row["phrase"],
                    )
                    for row in normalized_rows
                ],
            )
            if owns_connection:
                active_connection.commit()
            return normalized_rows
        except Exception:
            if owns_connection:
                active_connection.rollback()
            raise


def insert_rule_fvg_row(
    row: Mapping[str, str],
    connection: Connection | None = None,
) -> RuleFvgRow:
    inserted_row = {
        "id": row["id"],
        "rule_id": row["rule_id"],
        "verb": row["verb"],
        "phrase": row["phrase"],
    }
    owns_connection = connection is None

    with _use_connection(connection) as active_connection:
        try:
            active_connection.execute(
                f"""
                INSERT INTO {RULE_FVG_TABLE_NAME} (
                    id,
                    rule_id,
                    verb,
                    phrase
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    inserted_row["id"],
                    inserted_row["rule_id"],
                    inserted_row["verb"],
                    inserted_row["phrase"],
                ),
            )
            if owns_connection:
                active_connection.commit()
            return inserted_row
        except Exception:
            if owns_connection:
                active_connection.rollback()
            raise


def get_rule_fvg_row_by_id(
    rule_fvg_id: str,
    connection: Connection | None = None,
) -> RuleFvgRow | None:
    with _use_connection(connection) as active_connection:
        row = active_connection.execute(
            f"""
            SELECT
                id,
                rule_id,
                verb,
                phrase
            FROM {RULE_FVG_TABLE_NAME}
            WHERE id = ?
            """,
            (rule_fvg_id,),
        ).fetchone()
        if row is None:
            return None
        return _map_rule_fvg_row(row)


def list_rule_fvg_rows_by_rule_id(
    rule_id: str,
    connection: Connection | None = None,
) -> list[RuleFvgRow]:
    with _use_connection(connection) as active_connection:
        rows = active_connection.execute(
            f"""
            SELECT
                id,
                rule_id,
                verb,
                phrase
            FROM {RULE_FVG_TABLE_NAME}
            WHERE rule_id = ?
            ORDER BY rowid ASC
            """,
            (rule_id,),
        ).fetchall()
        return [_map_rule_fvg_row(row) for row in rows]


def update_rule_fvg_row(
    rule_fvg_id: str,
    verb: str,
    phrase: str,
    connection: Connection | None = None,
) -> RuleFvgRow:
    owns_connection = connection is None

    with _use_connection(connection) as active_connection:
        try:
            cursor = active_connection.execute(
                f"""
                UPDATE {RULE_FVG_TABLE_NAME}
                SET
                    verb = ?,
                    phrase = ?
                WHERE id = ?
                """,
                (verb, phrase, rule_fvg_id),
            )
            if cursor.rowcount <= 0:
                raise FileNotFoundError(f"Rule FVG row not found: {rule_fvg_id}")

            row = active_connection.execute(
                f"""
                SELECT
                    id,
                    rule_id,
                    verb,
                    phrase
                FROM {RULE_FVG_TABLE_NAME}
                WHERE id = ?
                """,
                (rule_fvg_id,),
            ).fetchone()
            if row is None:
                raise FileNotFoundError(f"Rule FVG row not found after update: {rule_fvg_id}")

            if owns_connection:
                active_connection.commit()
            return _map_rule_fvg_row(row)
        except Exception:
            if owns_connection:
                active_connection.rollback()
            raise


def remove_rule_fvg_row(
    rule_fvg_id: str,
    connection: Connection | None = None,
) -> bool:
    owns_connection = connection is None

    with _use_connection(connection) as active_connection:
        try:
            cursor = active_connection.execute(
                f"""
                DELETE FROM {RULE_FVG_TABLE_NAME}
                WHERE id = ?
                """,
                (rule_fvg_id,),
            )
            if owns_connection:
                active_connection.commit()
            return cursor.rowcount > 0
        except Exception:
            if owns_connection:
                active_connection.rollback()
            raise


def remove_rule_fvg_rows_by_rule_id(
    rule_id: str,
    connection: Connection | None = None,
) -> int:
    owns_connection = connection is None

    with _use_connection(connection) as active_connection:
        try:
            cursor = active_connection.execute(
                f"""
                DELETE FROM {RULE_FVG_TABLE_NAME}
                WHERE rule_id = ?
                """,
                (rule_id,),
            )
            if owns_connection:
                active_connection.commit()
            return cursor.rowcount
        except Exception:
            if owns_connection:
                active_connection.rollback()
            raise
