from collections.abc import Generator, Mapping
from contextlib import contextmanager
from sqlite3 import Connection, Row

from app.infrastructure.db.connection import connection_scope

RULES_TABLE_NAME = "rules"

RuleRow = dict[str, str]


def _map_rule_row(row: Row) -> RuleRow:
    return {
        "id": row["id"],
        "type": row["type"],
        "path": row["path"],
    }


@contextmanager
def _use_connection(connection: Connection | None) -> Generator[Connection, None, None]:
    if connection is not None:
        yield connection
        return

    with connection_scope() as scoped_connection:
        yield scoped_connection


def insert_rule(
    rule: Mapping[str, str],
    connection: Connection | None = None,
) -> RuleRow:
    inserted_rule = {
        "id": rule["id"],
        "type": rule["type"],
        "path": rule["path"],
    }
    owns_connection = connection is None

    with _use_connection(connection) as active_connection:
        try:
            active_connection.execute(
                f"""
                INSERT INTO {RULES_TABLE_NAME} (
                    id,
                    type,
                    path
                ) VALUES (?, ?, ?)
                """,
                (
                    inserted_rule["id"],
                    inserted_rule["type"],
                    inserted_rule["path"],
                ),
            )
            if owns_connection:
                active_connection.commit()
            return inserted_rule
        except Exception:
            if owns_connection:
                active_connection.rollback()
            raise


def get_rule_by_id(
    rule_id: str,
    connection: Connection | None = None,
) -> RuleRow | None:
    with _use_connection(connection) as active_connection:
        row = active_connection.execute(
            f"""
            SELECT
                id,
                type,
                path
            FROM {RULES_TABLE_NAME}
            WHERE id = ?
            """,
            (rule_id,),
        ).fetchone()
        if row is None:
            return None

        return _map_rule_row(row)


def get_all_rules(connection: Connection | None = None) -> list[RuleRow]:
    with _use_connection(connection) as active_connection:
        rows = active_connection.execute(
            f"""
            SELECT
                id,
                type,
                path
            FROM {RULES_TABLE_NAME}
            ORDER BY rowid DESC
            """
        ).fetchall()
        return [_map_rule_row(row) for row in rows]


def remove_rule(
    rule_id: str,
    connection: Connection | None = None,
) -> bool:
    owns_connection = connection is None

    with _use_connection(connection) as active_connection:
        try:
            cursor = active_connection.execute(
                f"""
                DELETE FROM {RULES_TABLE_NAME}
                WHERE id = ?
                """,
                (rule_id,),
            )
            if owns_connection:
                active_connection.commit()
            return cursor.rowcount > 0
        except Exception:
            if owns_connection:
                active_connection.rollback()
            raise


def get_existing_rule_for_import(
    rule_id: str,
    rule_type: str,
    path: str,
    connection: Connection | None = None,
) -> RuleRow | None:
    with _use_connection(connection) as active_connection:
        row = active_connection.execute(
            f"""
            SELECT
                id,
                type,
                path
            FROM {RULES_TABLE_NAME}
            WHERE id = ?
               OR (type = ? AND path = ?)
            ORDER BY CASE WHEN id = ? THEN 0 ELSE 1 END
            LIMIT 1
            """,
            (rule_id, rule_type, path, rule_id),
        ).fetchone()
        if row is None:
            return None

        return _map_rule_row(row)


def insert_rule_if_missing(
    rule: Mapping[str, str],
    connection: Connection | None = None,
) -> tuple[RuleRow, bool]:
    existing = get_existing_rule_for_import(
        rule_id=rule["id"],
        rule_type=rule["type"],
        path=rule["path"],
        connection=connection,
    )
    if existing is not None:
        return existing, False

    inserted = insert_rule(rule=rule, connection=connection)
    return inserted, True
