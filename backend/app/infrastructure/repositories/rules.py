from collections.abc import Generator, Mapping
from contextlib import contextmanager
from sqlite3 import Connection

from sqlalchemy import case, delete, insert, or_, select

from app.infrastructure.db.connection import connection_scope
from app.infrastructure.repositories._sqlalchemy import execute, rules_table

RuleRow = dict[str, str]


def _map_rule_row(row: Mapping[str, object]) -> RuleRow:
    return {
        "id": str(row["id"]),
        "version_id": str(row["version_id"]),
        "type": str(row["type"]),
        "path": str(row["path"]),
    }


@contextmanager
def _use_connection(connection: Connection | None) -> Generator[Connection, None, None]:
    if connection is not None:
        yield connection
        return

    with connection_scope() as scoped_connection:
        yield scoped_connection


def write_rule_item(
    rule: Mapping[str, str],
    connection: Connection | None = None,
) -> RuleRow:
    written = {
        "id": str(rule["id"]),
        "version_id": str(rule["version_id"]),
        "type": str(rule["type"]),
        "path": str(rule["path"]),
    }

    owns_connection = connection is None
    with _use_connection(connection) as active_connection:
        try:
            execute(active_connection, insert(rules_table).values(**written))
            if owns_connection:
                active_connection.commit()
            return written
        except Exception:
            if owns_connection:
                active_connection.rollback()
            raise


def get_rule_by_id(
    rule_id: str,
    connection: Connection | None = None,
) -> RuleRow | None:
    statement = (
        select(
            rules_table.c.id,
            rules_table.c.version_id,
            rules_table.c.type,
            rules_table.c.path,
        )
        .select_from(rules_table)
        .where(rules_table.c.id == rule_id)
    )
    with _use_connection(connection) as active_connection:
        row = execute(active_connection, statement).fetchone()

    if row is None:
        return None
    return _map_rule_row(row)


def read_all_rules(connection: Connection | None = None) -> list[RuleRow]:
    statement = (
        select(
            rules_table.c.id,
            rules_table.c.version_id,
            rules_table.c.type,
            rules_table.c.path,
        )
        .select_from(rules_table)
        .order_by(rules_table.c.id.desc())
    )
    with _use_connection(connection) as active_connection:
        rows = execute(active_connection, statement).fetchall()

    return [_map_rule_row(row) for row in rows]


def rm_rule_item(
    rule_id: str,
    connection: Connection | None = None,
) -> bool:
    owns_connection = connection is None
    with _use_connection(connection) as active_connection:
        try:
            cursor = execute(
                active_connection,
                delete(rules_table).where(rules_table.c.id == rule_id),
            )
            if owns_connection:
                active_connection.commit()
            return cursor.rowcount > 0
        except Exception:
            if owns_connection:
                active_connection.rollback()
            raise


def get_existing_rule_for_import(
    *,
    rule_id: str,
    rule_type: str,
    path: str,
    connection: Connection | None = None,
) -> RuleRow | None:
    statement = (
        select(
            rules_table.c.id,
            rules_table.c.version_id,
            rules_table.c.type,
            rules_table.c.path,
        )
        .select_from(rules_table)
        .where(
            or_(
                rules_table.c.id == rule_id,
                (rules_table.c.type == rule_type) & (rules_table.c.path == path),
            )
        )
        .order_by(case((rules_table.c.id == rule_id, 0), else_=1))
        .limit(1)
    )
    with _use_connection(connection) as active_connection:
        row = execute(active_connection, statement).fetchone()

    if row is None:
        return None
    return _map_rule_row(row)
