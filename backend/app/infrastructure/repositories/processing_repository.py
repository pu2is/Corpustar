import json
from collections.abc import Mapping
from datetime import datetime, timezone
from sqlite3 import Row
from typing import Any
from uuid import uuid4

from app.infrastructure.db.connection import connection_scope
from app.schemas.processings import ProcessingState, ProcessingType

PROCESSINGS_TABLE_NAME = "processings"

ProcessingRow = dict[str, str | None]
ProcessingDto = dict[str, Any]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _map_processing_row(row: Row) -> ProcessingRow:
    return {
        "id": row["id"],
        "doc_id": row["doc_id"],
        "type": row["type"],
        "state": row["state"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "error_message": row["error_message"],
        "meta_json": row["meta_json"],
    }


def _parse_meta(meta_json: str | None) -> dict[str, Any] | None:
    if meta_json is None:
        return None

    parsed = json.loads(meta_json)
    if isinstance(parsed, dict):
        return parsed
    return {"value": parsed}


def map_processing_row_to_dto(processing_row: Mapping[str, str | None]) -> ProcessingDto:
    return {
        "id": processing_row["id"],
        "docId": processing_row["doc_id"],
        "type": processing_row["type"],
        "state": processing_row["state"],
        "createdAt": processing_row["created_at"],
        "updatedAt": processing_row["updated_at"],
        "errorMessage": processing_row["error_message"],
        "meta": _parse_meta(processing_row["meta_json"]),
    }


def create_processing(
    doc_id: str,
    type: ProcessingType,
    state: ProcessingState = "running",
    meta_json: str | None = None,
) -> ProcessingRow:
    now_iso = _now_iso()
    processing = {
        "id": str(uuid4()),
        "doc_id": doc_id,
        "type": type,
        "state": state,
        "created_at": now_iso,
        "updated_at": now_iso,
        "error_message": None,
        "meta_json": meta_json,
    }

    with connection_scope() as connection:
        connection.execute(
            f"""
            INSERT INTO {PROCESSINGS_TABLE_NAME} (
                id,
                doc_id,
                type,
                state,
                created_at,
                updated_at,
                error_message,
                meta_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                processing["id"],
                processing["doc_id"],
                processing["type"],
                processing["state"],
                processing["created_at"],
                processing["updated_at"],
                processing["error_message"],
                processing["meta_json"],
            ),
        )
        connection.commit()
        return processing


def update_processing_state(processing_id: str, new_state: ProcessingState, error_message: str | None = None) -> ProcessingRow:
    updated_at = _now_iso()

    with connection_scope() as connection:
        cursor = connection.execute(
            f"""
            UPDATE {PROCESSINGS_TABLE_NAME}
            SET
                state = ?,
                updated_at = ?,
                error_message = ?
            WHERE id = ?
            """,
            (new_state, updated_at, error_message, processing_id),
        )
        if cursor.rowcount <= 0:
            connection.rollback()
            raise FileNotFoundError(f"Processing not found: {processing_id}")

        row = connection.execute(
            f"""
            SELECT
                id,
                doc_id,
                type,
                state,
                created_at,
                updated_at,
                error_message,
                meta_json
            FROM {PROCESSINGS_TABLE_NAME}
            WHERE id = ?
            """,
            (processing_id,),
        ).fetchone()
        if row is None:
            connection.rollback()
            raise FileNotFoundError(f"Processing not found after update: {processing_id}")

        connection.commit()
        return _map_processing_row(row)


def get_processing_by_id(processing_id: str) -> ProcessingRow | None:
    with connection_scope() as connection:
        row = connection.execute(
            f"""
            SELECT
                id,
                doc_id,
                type,
                state,
                created_at,
                updated_at,
                error_message,
                meta_json
            FROM {PROCESSINGS_TABLE_NAME}
            WHERE id = ?
            """,
            (processing_id,),
        ).fetchone()
        if row is None:
            return None
        return _map_processing_row(row)


def list_processings() -> list[ProcessingRow]:
    with connection_scope() as connection:
        rows = connection.execute(
            f"""
            SELECT
                id,
                doc_id,
                type,
                state,
                created_at,
                updated_at,
                error_message,
                meta_json
            FROM {PROCESSINGS_TABLE_NAME}
            ORDER BY created_at DESC
            """
        ).fetchall()
        return [_map_processing_row(row) for row in rows]


def list_processings_by_doc_id(doc_id: str) -> list[ProcessingRow]:
    with connection_scope() as connection:
        rows = connection.execute(
            f"""
            SELECT
                id,
                doc_id,
                type,
                state,
                created_at,
                updated_at,
                error_message,
                meta_json
            FROM {PROCESSINGS_TABLE_NAME}
            WHERE doc_id = ?
            ORDER BY created_at DESC
            """,
            (doc_id,),
        ).fetchall()
        return [_map_processing_row(row) for row in rows]


def list_processings_by_doc_id_and_type(
    doc_id: str,
    processing_type: ProcessingType = "sentence_segmentation",
    state: ProcessingState | None = "succeed",
) -> list[ProcessingRow]:
    parameters: list[str] = [doc_id, processing_type]
    state_sql = ""
    if state is not None:
        state_sql = "AND state = ?"
        parameters.append(state)

    with connection_scope() as connection:
        rows = connection.execute(
            f"""
            SELECT
                id,
                doc_id,
                type,
                state,
                created_at,
                updated_at,
                error_message,
                meta_json
            FROM {PROCESSINGS_TABLE_NAME}
            WHERE doc_id = ?
              AND type = ?
              {state_sql}
            ORDER BY created_at DESC
            """,
            tuple(parameters),
        ).fetchall()
        return [_map_processing_row(row) for row in rows]


def get_latest_processing_by_doc_id_and_type(
    doc_id: str,
    processing_type: ProcessingType = "sentence_segmentation",
    state: ProcessingState | None = "succeed",
) -> ProcessingRow | None:
    parameters: list[str] = [doc_id, processing_type]
    state_sql = ""
    if state is not None:
        state_sql = "AND state = ?"
        parameters.append(state)

    with connection_scope() as connection:
        row = connection.execute(
            f"""
            SELECT
                id,
                doc_id,
                type,
                state,
                created_at,
                updated_at,
                error_message,
                meta_json
            FROM {PROCESSINGS_TABLE_NAME}
            WHERE doc_id = ?
              AND type = ?
              {state_sql}
            ORDER BY created_at DESC
            LIMIT 1
            """,
            tuple(parameters),
        ).fetchone()
        if row is None:
            return None
        return _map_processing_row(row)
