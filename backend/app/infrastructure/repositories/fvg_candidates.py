from collections.abc import Generator, Iterable, Mapping
from contextlib import contextmanager
from sqlite3 import Connection
from typing import Any

from sqlalchemy import bindparam, delete, insert, select, update

from app.infrastructure.db.connection import connection_scope
from app.infrastructure.repositories._sqlalchemy import (
    execute,
    execute_many,
    fvg_candidates_table,
)

FvgCandidateRow = dict[str, int | str | bool]


def _to_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    return int(value)


def _to_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    return bool(int(value))


def _map_fvg_candidate_row(row: Mapping[str, Any]) -> FvgCandidateRow:
    return {
        "id": _to_str(row["id"]),
        "sentence_id": _to_str(row["sentence_id"]),
        "process_id": _to_str(row["process_id"]),
        "algo_fvg_entry_id": _to_str(row["algo_fvg_entry_id"]),
        "corrected_fvg_entry_id": _to_str(row["corrected_fvg_entry_id"]),
        "algo_verb_token": _to_str(row["algo_verb_token"]),
        "algo_verb_index": _to_int(row["algo_verb_index"], -1),
        "corrected_verb_token": _to_str(row["corrected_verb_token"]),
        "corrected_verb_index": _to_int(row["corrected_verb_index"], -1),
        "algo_noun_token": _to_str(row["algo_noun_token"]),
        "algo_noun_index": _to_int(row["algo_noun_index"], -1),
        "corrected_noun_token": _to_str(row["corrected_noun_token"]),
        "corrected_noun_index": _to_int(row["corrected_noun_index"], -1),
        "algo_prep_token": _to_str(row["algo_prep_token"]),
        "algo_prep_index": _to_int(row["algo_prep_index"], -1),
        "corrected_prep_token": _to_str(row["corrected_prep_token"]),
        "corrected_prep_index": _to_int(row["corrected_prep_index"], -1),
        "label": _to_str(row["label"]),
        "manuelle_created": _to_bool(row["manuelle_created"]),
        "removed": _to_bool(row["removed"]),
    }


def _normalize_fvg_candidate_row(row: Mapping[str, int | str | bool]) -> FvgCandidateRow:
    return {
        "id": _to_str(row.get("id")),
        "sentence_id": _to_str(row.get("sentence_id")),
        "process_id": _to_str(row.get("process_id")),
        "algo_fvg_entry_id": _to_str(row.get("algo_fvg_entry_id")),
        "corrected_fvg_entry_id": _to_str(row.get("corrected_fvg_entry_id")),
        "algo_verb_token": _to_str(row.get("algo_verb_token")),
        "algo_verb_index": _to_int(row.get("algo_verb_index"), -1),
        "corrected_verb_token": _to_str(row.get("corrected_verb_token")),
        "corrected_verb_index": _to_int(row.get("corrected_verb_index"), -1),
        "algo_noun_token": _to_str(row.get("algo_noun_token")),
        "algo_noun_index": _to_int(row.get("algo_noun_index"), -1),
        "corrected_noun_token": _to_str(row.get("corrected_noun_token")),
        "corrected_noun_index": _to_int(row.get("corrected_noun_index"), -1),
        "algo_prep_token": _to_str(row.get("algo_prep_token")),
        "algo_prep_index": _to_int(row.get("algo_prep_index"), -1),
        "corrected_prep_token": _to_str(row.get("corrected_prep_token")),
        "corrected_prep_index": _to_int(row.get("corrected_prep_index"), -1),
        "label": _to_str(row.get("label")),
        "manuelle_created": bool(row.get("manuelle_created", False)),
        "removed": bool(row.get("removed", False)),
    }


@contextmanager
def _use_connection(connection: Connection | None) -> Generator[Connection, None, None]:
    if connection is not None:
        yield connection
        return

    with connection_scope() as scoped_connection:
        yield scoped_connection


def write_fvg_candidate_item(
    row: Mapping[str, int | str | bool],
    connection: Connection | None = None,
) -> FvgCandidateRow:
    normalized = _normalize_fvg_candidate_row(row)

    statement = insert(fvg_candidates_table).values(
        **{
            **normalized,
            "manuelle_created": int(bool(normalized["manuelle_created"])),
            "removed": int(bool(normalized["removed"])),
        }
    )

    owns_connection = connection is None
    with _use_connection(connection) as active_connection:
        try:
            execute(active_connection, statement)
            if owns_connection:
                active_connection.commit()
            return normalized
        except Exception:
            if owns_connection:
                active_connection.rollback()
            raise


def write_fvg_candidate_items(
    rows: Iterable[Mapping[str, int | str | bool]],
    *,
    clear_sentence_ids: list[str] | None = None,
    clear_process_id: str | None = None,
    connection: Connection | None = None,
) -> list[FvgCandidateRow]:
    normalized_rows = [_normalize_fvg_candidate_row(row) for row in rows]

    owns_connection = connection is None
    with _use_connection(connection) as active_connection:
        try:
            if clear_sentence_ids:
                _rm_fvg_candidate_items_by_sentence_ids(
                    clear_sentence_ids,
                    process_id=clear_process_id,
                    connection=active_connection,
                )

            if normalized_rows:
                statement = insert(fvg_candidates_table).values(
                    id=bindparam("id"),
                    sentence_id=bindparam("sentence_id"),
                    process_id=bindparam("process_id"),
                    algo_fvg_entry_id=bindparam("algo_fvg_entry_id"),
                    corrected_fvg_entry_id=bindparam("corrected_fvg_entry_id"),
                    algo_verb_token=bindparam("algo_verb_token"),
                    algo_verb_index=bindparam("algo_verb_index"),
                    corrected_verb_token=bindparam("corrected_verb_token"),
                    corrected_verb_index=bindparam("corrected_verb_index"),
                    algo_noun_token=bindparam("algo_noun_token"),
                    algo_noun_index=bindparam("algo_noun_index"),
                    corrected_noun_token=bindparam("corrected_noun_token"),
                    corrected_noun_index=bindparam("corrected_noun_index"),
                    algo_prep_token=bindparam("algo_prep_token"),
                    algo_prep_index=bindparam("algo_prep_index"),
                    corrected_prep_token=bindparam("corrected_prep_token"),
                    corrected_prep_index=bindparam("corrected_prep_index"),
                    label=bindparam("label"),
                    manuelle_created=bindparam("manuelle_created"),
                    removed=bindparam("removed"),
                )
                execute_many(
                    active_connection,
                    statement,
                    [
                        {
                            **normalized,
                            "manuelle_created": int(bool(normalized["manuelle_created"])),
                            "removed": int(bool(normalized["removed"])),
                        }
                        for normalized in normalized_rows
                    ],
                )

            if owns_connection:
                active_connection.commit()
            return normalized_rows
        except Exception:
            if owns_connection:
                active_connection.rollback()
            raise


def get_fvg_candidate_items_by_sentence_id(
    sentence_id: str,
    process_id: str | None = None,
    connection: Connection | None = None,
) -> list[FvgCandidateRow]:
    statement = (
        select(
            fvg_candidates_table.c.id,
            fvg_candidates_table.c.sentence_id,
            fvg_candidates_table.c.process_id,
            fvg_candidates_table.c.algo_fvg_entry_id,
            fvg_candidates_table.c.corrected_fvg_entry_id,
            fvg_candidates_table.c.algo_verb_token,
            fvg_candidates_table.c.algo_verb_index,
            fvg_candidates_table.c.corrected_verb_token,
            fvg_candidates_table.c.corrected_verb_index,
            fvg_candidates_table.c.algo_noun_token,
            fvg_candidates_table.c.algo_noun_index,
            fvg_candidates_table.c.corrected_noun_token,
            fvg_candidates_table.c.corrected_noun_index,
            fvg_candidates_table.c.algo_prep_token,
            fvg_candidates_table.c.algo_prep_index,
            fvg_candidates_table.c.corrected_prep_token,
            fvg_candidates_table.c.corrected_prep_index,
            fvg_candidates_table.c.label,
            fvg_candidates_table.c.manuelle_created,
            fvg_candidates_table.c.removed,
        )
        .select_from(fvg_candidates_table)
    )
    if process_id is None:
        statement = statement.where(fvg_candidates_table.c.sentence_id == sentence_id)
    else:
        statement = statement.where(
            (fvg_candidates_table.c.sentence_id == sentence_id)
            & (fvg_candidates_table.c.process_id == process_id)
        )

    statement = statement.order_by(fvg_candidates_table.c.algo_verb_index.asc(), fvg_candidates_table.c.id.asc())

    with _use_connection(connection) as active_connection:
        rows = execute(active_connection, statement).fetchall()
    return [_map_fvg_candidate_row(row) for row in rows]


def get_fvg_candidate_items_by_sentence_ids(
    sentence_ids: list[str],
) -> dict[str, list[FvgCandidateRow]]:
    if not sentence_ids:
        return {}

    unique_sentence_ids = list(dict.fromkeys(sentence_ids))
    statement = (
        select(
            fvg_candidates_table.c.id,
            fvg_candidates_table.c.sentence_id,
            fvg_candidates_table.c.process_id,
            fvg_candidates_table.c.algo_fvg_entry_id,
            fvg_candidates_table.c.corrected_fvg_entry_id,
            fvg_candidates_table.c.algo_verb_token,
            fvg_candidates_table.c.algo_verb_index,
            fvg_candidates_table.c.corrected_verb_token,
            fvg_candidates_table.c.corrected_verb_index,
            fvg_candidates_table.c.algo_noun_token,
            fvg_candidates_table.c.algo_noun_index,
            fvg_candidates_table.c.corrected_noun_token,
            fvg_candidates_table.c.corrected_noun_index,
            fvg_candidates_table.c.algo_prep_token,
            fvg_candidates_table.c.algo_prep_index,
            fvg_candidates_table.c.corrected_prep_token,
            fvg_candidates_table.c.corrected_prep_index,
            fvg_candidates_table.c.label,
            fvg_candidates_table.c.manuelle_created,
            fvg_candidates_table.c.removed,
        )
        .select_from(fvg_candidates_table)
        .where(fvg_candidates_table.c.sentence_id.in_(unique_sentence_ids))
        .order_by(
            fvg_candidates_table.c.sentence_id.asc(),
            fvg_candidates_table.c.algo_verb_index.asc(),
            fvg_candidates_table.c.id.asc(),
        )
    )

    with connection_scope() as connection:
        rows = execute(connection, statement).fetchall()

    result: dict[str, list[FvgCandidateRow]] = {sentence_id: [] for sentence_id in unique_sentence_ids}
    for row in rows:
        mapped = _map_fvg_candidate_row(row)
        result.setdefault(str(mapped["sentence_id"]), []).append(mapped)
    return result


def get_fvg_candidate_items_by_process_id(
    process_id: str,
    *,
    connection: Connection | None = None,
) -> list[FvgCandidateRow]:
    statement = (
        select(
            fvg_candidates_table.c.id,
            fvg_candidates_table.c.sentence_id,
            fvg_candidates_table.c.process_id,
            fvg_candidates_table.c.algo_fvg_entry_id,
            fvg_candidates_table.c.corrected_fvg_entry_id,
            fvg_candidates_table.c.algo_verb_token,
            fvg_candidates_table.c.algo_verb_index,
            fvg_candidates_table.c.corrected_verb_token,
            fvg_candidates_table.c.corrected_verb_index,
            fvg_candidates_table.c.algo_noun_token,
            fvg_candidates_table.c.algo_noun_index,
            fvg_candidates_table.c.corrected_noun_token,
            fvg_candidates_table.c.corrected_noun_index,
            fvg_candidates_table.c.algo_prep_token,
            fvg_candidates_table.c.algo_prep_index,
            fvg_candidates_table.c.corrected_prep_token,
            fvg_candidates_table.c.corrected_prep_index,
            fvg_candidates_table.c.label,
            fvg_candidates_table.c.manuelle_created,
            fvg_candidates_table.c.removed,
        )
        .select_from(fvg_candidates_table)
        .where(fvg_candidates_table.c.process_id == process_id)
        .order_by(
            fvg_candidates_table.c.sentence_id.asc(),
            fvg_candidates_table.c.algo_verb_index.asc(),
            fvg_candidates_table.c.id.asc(),
        )
    )

    with _use_connection(connection) as active_connection:
        rows = execute(active_connection, statement).fetchall()
    return [_map_fvg_candidate_row(row) for row in rows]


def change_fvg_candidate_item(
    candidate_id: str,
    *,
    corrected_verb_token: str | None = None,
    corrected_verb_index: int | None = None,
    corrected_noun_token: str | None = None,
    corrected_noun_index: int | None = None,
    corrected_prep_token: str | None = None,
    corrected_prep_index: int | None = None,
    corrected_fvg_entry_id: str | None = None,
    label: str | None = None,
    manuelle_created: bool | None = None,
    removed: bool | None = None,
    connection: Connection | None = None,
) -> FvgCandidateRow:
    values_to_update: dict[str, int | str] = {}
    if corrected_verb_token is not None:
        values_to_update["corrected_verb_token"] = corrected_verb_token
    if corrected_verb_index is not None:
        values_to_update["corrected_verb_index"] = corrected_verb_index
    if corrected_noun_token is not None:
        values_to_update["corrected_noun_token"] = corrected_noun_token
    if corrected_noun_index is not None:
        values_to_update["corrected_noun_index"] = corrected_noun_index
    if corrected_prep_token is not None:
        values_to_update["corrected_prep_token"] = corrected_prep_token
    if corrected_prep_index is not None:
        values_to_update["corrected_prep_index"] = corrected_prep_index
    if corrected_fvg_entry_id is not None:
        values_to_update["corrected_fvg_entry_id"] = corrected_fvg_entry_id
    if label is not None:
        values_to_update["label"] = label
    if manuelle_created is not None:
        values_to_update["manuelle_created"] = int(bool(manuelle_created))
    if removed is not None:
        values_to_update["removed"] = int(bool(removed))

    owns_connection = connection is None
    with _use_connection(connection) as active_connection:
        try:
            if values_to_update:
                cursor = execute(
                    active_connection,
                    update(fvg_candidates_table)
                    .where(fvg_candidates_table.c.id == candidate_id)
                    .values(**values_to_update),
                )
                if cursor.rowcount <= 0:
                    raise FileNotFoundError(f"FVG candidate not found: {candidate_id}")

            row = _get_fvg_candidate_item_by_id(candidate_id, connection=active_connection)
            if row is None:
                raise FileNotFoundError(f"FVG candidate not found: {candidate_id}")

            if owns_connection:
                active_connection.commit()
            return row
        except Exception:
            if owns_connection:
                active_connection.rollback()
            raise


def _get_fvg_candidate_item_by_id(
    candidate_id: str,
    *,
    connection: Connection,
) -> FvgCandidateRow | None:
    statement = (
        select(
            fvg_candidates_table.c.id,
            fvg_candidates_table.c.sentence_id,
            fvg_candidates_table.c.process_id,
            fvg_candidates_table.c.algo_fvg_entry_id,
            fvg_candidates_table.c.corrected_fvg_entry_id,
            fvg_candidates_table.c.algo_verb_token,
            fvg_candidates_table.c.algo_verb_index,
            fvg_candidates_table.c.corrected_verb_token,
            fvg_candidates_table.c.corrected_verb_index,
            fvg_candidates_table.c.algo_noun_token,
            fvg_candidates_table.c.algo_noun_index,
            fvg_candidates_table.c.corrected_noun_token,
            fvg_candidates_table.c.corrected_noun_index,
            fvg_candidates_table.c.algo_prep_token,
            fvg_candidates_table.c.algo_prep_index,
            fvg_candidates_table.c.corrected_prep_token,
            fvg_candidates_table.c.corrected_prep_index,
            fvg_candidates_table.c.label,
            fvg_candidates_table.c.manuelle_created,
            fvg_candidates_table.c.removed,
        )
        .select_from(fvg_candidates_table)
        .where(fvg_candidates_table.c.id == candidate_id)
    )
    row = execute(connection, statement).fetchone()
    if row is None:
        return None
    return _map_fvg_candidate_row(row)


def _rm_fvg_candidate_items_by_sentence_ids(
    sentence_ids: list[str],
    *,
    process_id: str | None,
    connection: Connection,
) -> int:
    if not sentence_ids:
        return 0

    unique_ids = list(dict.fromkeys(sentence_ids))
    where_clause = fvg_candidates_table.c.sentence_id.in_(unique_ids)
    if process_id is not None:
        where_clause = where_clause & (fvg_candidates_table.c.process_id == process_id)

    cursor = execute(connection, delete(fvg_candidates_table).where(where_clause))
    return cursor.rowcount
