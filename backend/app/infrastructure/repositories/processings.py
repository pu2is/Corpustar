import json
from collections.abc import Mapping
from datetime import datetime, timezone
from sqlite3 import Connection
from typing import Any
from uuid import uuid4

from sqlalchemy import delete, insert, select, update

from app.infrastructure.db.connection import connection_scope
from app.infrastructure.repositories._sqlalchemy import execute, processings_table

ProcessRow = dict[str, str | None]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _map_process_row(row: Mapping[str, Any]) -> ProcessRow:
    return {
        "id": str(row["id"]),
        "parent_id": str(row["parent_id"]),
        "doc_id": str(row["doc_id"]) if row["doc_id"] is not None else None,
        "type": str(row["type"]),
        "state": str(row["state"]),
        "created_at": str(row["created_at"]),
        "updated_at": str(row["updated_at"]),
        "error_message": str(row["error_message"]) if row["error_message"] is not None else None,
        "meta_json": str(row["meta_json"]) if row["meta_json"] is not None else None,
    }


def parse_meta_json(meta_json: str | None) -> dict[str, Any] | None:
    if not meta_json:
        return None

    parsed = json.loads(meta_json)
    if isinstance(parsed, dict):
        return parsed

    return {"value": parsed}


def map_process_row_to_item(process_row: Mapping[str, str | None]) -> dict[str, Any]:
    return {
        "id": process_row["id"],
        "parent_id": process_row["parent_id"],
        "doc_id": process_row["doc_id"],
        "type": process_row["type"],
        "state": process_row["state"],
        "created_at": process_row["created_at"],
        "updated_at": process_row["updated_at"],
        "error_message": process_row["error_message"],
        "meta_json": process_row["meta_json"],
        "meta": parse_meta_json(process_row["meta_json"]),
    }


def write_process_item(
    *,
    doc_id: str | None,
    type: str,
    state: str = "running",
    parent_id: str | None = None,
    error_message: str | None = None,
    meta_json: str | None = None,
    process_id: str | None = None,
    connection: Connection | None = None,
) -> ProcessRow:
    now_iso = _now_iso()
    resolved_process_id = process_id or str(uuid4())
    resolved_parent_id = parent_id or resolved_process_id

    process: ProcessRow = {
        "id": resolved_process_id,
        "parent_id": resolved_parent_id,
        "doc_id": doc_id,
        "type": type,
        "state": state,
        "created_at": now_iso,
        "updated_at": now_iso,
        "error_message": error_message,
        "meta_json": meta_json,
    }

    statement = insert(processings_table).values(**process)
    if connection is None:
        with connection_scope() as scoped_connection:
            execute(scoped_connection, statement)
            scoped_connection.commit()
        return process

    execute(connection, statement)
    return process


def change_process_item_state(
    process_id: str,
    new_state: str,
    error_message: str | None = None,
    connection: Connection | None = None,
) -> ProcessRow:
    updated_at = _now_iso()

    if connection is None:
        with connection_scope() as scoped_connection:
            process = _change_process_item_state_with_connection(
                scoped_connection,
                process_id,
                new_state,
                updated_at,
                error_message,
            )
            scoped_connection.commit()
            return process

    return _change_process_item_state_with_connection(
        connection,
        process_id,
        new_state,
        updated_at,
        error_message,
    )


def _change_process_item_state_with_connection(
    connection: Connection,
    process_id: str,
    new_state: str,
    updated_at: str,
    error_message: str | None,
) -> ProcessRow:
    cursor = execute(
        connection,
        update(processings_table)
        .where(processings_table.c.id == process_id)
        .values(
            state=new_state,
            updated_at=updated_at,
            error_message=error_message,
        ),
    )
    if cursor.rowcount <= 0:
        raise FileNotFoundError(f"Process item not found: {process_id}")

    process = read_process_item_by_id(process_id, connection=connection)
    if process is None:
        raise FileNotFoundError(f"Process item not found after update: {process_id}")
    return process


def read_process_item_by_id(process_id: str, connection: Connection | None = None) -> ProcessRow | None:
    statement = (
        select(
            processings_table.c.id,
            processings_table.c.parent_id,
            processings_table.c.doc_id,
            processings_table.c.type,
            processings_table.c.state,
            processings_table.c.created_at,
            processings_table.c.updated_at,
            processings_table.c.error_message,
            processings_table.c.meta_json,
        )
        .select_from(processings_table)
        .where(processings_table.c.id == process_id)
    )

    if connection is None:
        with connection_scope() as scoped_connection:
            return read_process_item_by_id(process_id, connection=scoped_connection)

    row = execute(connection, statement).fetchone()
    if row is None:
        return None
    return _map_process_row(row)


def get_all_processes() -> list[ProcessRow]:
    statement = (
        select(
            processings_table.c.id,
            processings_table.c.parent_id,
            processings_table.c.doc_id,
            processings_table.c.type,
            processings_table.c.state,
            processings_table.c.created_at,
            processings_table.c.updated_at,
            processings_table.c.error_message,
            processings_table.c.meta_json,
        )
        .select_from(processings_table)
        .order_by(processings_table.c.created_at.desc())
    )

    with connection_scope() as connection:
        rows = execute(connection, statement).fetchall()

    return [_map_process_row(row) for row in rows]


def rm_process_item(process_id: str, connection: Connection | None = None) -> bool:
    if connection is None:
        with connection_scope() as scoped_connection:
            deleted = rm_process_item(process_id, connection=scoped_connection)
            scoped_connection.commit()
            return deleted

    cursor = execute(
        connection,
        delete(processings_table).where(processings_table.c.id == process_id),
    )
    return cursor.rowcount > 0
