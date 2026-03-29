from collections.abc import Iterable, Iterator, Mapping
from sqlite3 import Connection
from uuid import uuid4

from sqlalchemy import bindparam, delete, insert, select, update

from app.infrastructure.db.connection import connection_scope, open_connection
from app.infrastructure.repositories._sqlalchemy import (
    execute,
    execute_many,
    sentences_table,
)

SentenceRow = dict[str, int | str]


def _map_sentence_row(row: Mapping[str, object]) -> SentenceRow:
    return {
        "id": str(row["id"]),
        "version_id": str(row["version_id"]),
        "doc_id": str(row["doc_id"]),
        "start_offset": int(row["start_offset"]),
        "end_offset": int(row["end_offset"]),
        "source_text": str(row["source_text"]),
        "corrected_text": str(row["corrected_text"]),
    }


def write_sentences_in_batch(
    *,
    version_id: str,
    doc_id: str,
    spans: Iterable[Mapping[str, int]],
    full_text: str,
) -> list[SentenceRow]:
    sentence_rows: list[SentenceRow] = []
    for span in spans:
        start_offset = int(span["start_offset"])
        end_offset = int(span["end_offset"])
        source_text = full_text[start_offset:end_offset]

        sentence_rows.append(
            {
                "id": str(uuid4()),
                "version_id": version_id,
                "doc_id": doc_id,
                "start_offset": start_offset,
                "end_offset": end_offset,
                "source_text": source_text,
                "corrected_text": source_text,
            }
        )

    if not sentence_rows:
        return []

    statement = insert(sentences_table).values(
        id=bindparam("id"),
        version_id=bindparam("version_id"),
        doc_id=bindparam("doc_id"),
        start_offset=bindparam("start_offset"),
        end_offset=bindparam("end_offset"),
        source_text=bindparam("source_text"),
        corrected_text=bindparam("corrected_text"),
    )
    with connection_scope() as connection:
        execute_many(connection, statement, sentence_rows)
        connection.commit()

    return sentence_rows


def read_sentences_by_version_cursor(
    *,
    doc_id: str,
    version_id: str,
    after_start_offset: int | None,
    limit: int | None,
) -> list[SentenceRow]:
    if limit is not None and limit <= 0:
        return []

    statement = (
        select(
            sentences_table.c.id,
            sentences_table.c.version_id,
            sentences_table.c.doc_id,
            sentences_table.c.start_offset,
            sentences_table.c.end_offset,
            sentences_table.c.source_text,
            sentences_table.c.corrected_text,
        )
        .select_from(sentences_table)
        .where(
            (sentences_table.c.doc_id == doc_id)
            & (sentences_table.c.version_id == version_id)
        )
        .order_by(sentences_table.c.start_offset.asc())
    )
    if after_start_offset is not None:
        statement = statement.where(sentences_table.c.start_offset > after_start_offset)
    if limit is not None:
        statement = statement.limit(limit)

    with connection_scope() as connection:
        rows = execute(connection, statement).fetchall()

    return [_map_sentence_row(row) for row in rows]


def get_sentence_by_id(sentence_id: str, connection: Connection | None = None) -> SentenceRow | None:
    statement = (
        select(
            sentences_table.c.id,
            sentences_table.c.version_id,
            sentences_table.c.doc_id,
            sentences_table.c.start_offset,
            sentences_table.c.end_offset,
            sentences_table.c.source_text,
            sentences_table.c.corrected_text,
        )
        .select_from(sentences_table)
        .where(sentences_table.c.id == sentence_id)
    )

    if connection is None:
        with connection_scope() as scoped_connection:
            return get_sentence_by_id(sentence_id, connection=scoped_connection)

    row = execute(connection, statement).fetchone()
    if row is None:
        return None
    return _map_sentence_row(row)


def get_sentences_by_ids(sentence_ids: list[str], connection: Connection | None = None) -> list[SentenceRow]:
    if not sentence_ids:
        return []

    statement = (
        select(
            sentences_table.c.id,
            sentences_table.c.version_id,
            sentences_table.c.doc_id,
            sentences_table.c.start_offset,
            sentences_table.c.end_offset,
            sentences_table.c.source_text,
            sentences_table.c.corrected_text,
        )
        .select_from(sentences_table)
        .where(sentences_table.c.id.in_(sentence_ids))
        .order_by(sentences_table.c.start_offset.asc())
    )

    if connection is None:
        with connection_scope() as scoped_connection:
            return get_sentences_by_ids(sentence_ids, connection=scoped_connection)

    rows = execute(connection, statement).fetchall()
    return [_map_sentence_row(row) for row in rows]


def get_all_sentences_by_version_id(
    version_id: str,
    fetch_batch_size: int = 512,
) -> Iterator[SentenceRow]:
    if not version_id:
        return

    statement = (
        select(
            sentences_table.c.id,
            sentences_table.c.version_id,
            sentences_table.c.doc_id,
            sentences_table.c.start_offset,
            sentences_table.c.end_offset,
            sentences_table.c.source_text,
            sentences_table.c.corrected_text,
        )
        .select_from(sentences_table)
        .where(sentences_table.c.version_id == version_id)
        .order_by(sentences_table.c.start_offset.asc())
    )

    connection = open_connection()
    try:
        cursor = execute(connection, statement)
        while True:
            rows = cursor.fetchmany(fetch_batch_size)
            if not rows:
                break

            for row in rows:
                yield _map_sentence_row(row)
    finally:
        connection.close()


def merge_sentences_to_one(
    sentence_ids: list[str],
    merged_sentence: Mapping[str, int | str],
    connection: Connection | None = None,
) -> None:
    if not sentence_ids:
        raise ValueError("sentence_ids is required")

    if connection is None:
        with connection_scope() as scoped_connection:
            merge_sentences_to_one(
                sentence_ids=sentence_ids,
                merged_sentence=merged_sentence,
                connection=scoped_connection,
            )
            scoped_connection.commit()
        return

    delete_cursor = execute(
        connection,
        delete(sentences_table).where(sentences_table.c.id.in_(sentence_ids)),
    )
    if delete_cursor.rowcount != len(sentence_ids):
        raise RuntimeError("Sentence merge failed: expected rows were not fully deleted")

    execute(connection, insert(sentences_table).values(**_normalize_sentence_row(merged_sentence)))


def replace_sentence_with_split(
    sentence_id: str,
    left_sentence: Mapping[str, int | str],
    right_sentence: Mapping[str, int | str],
    connection: Connection | None = None,
) -> None:
    if connection is None:
        with connection_scope() as scoped_connection:
            replace_sentence_with_split(
                sentence_id=sentence_id,
                left_sentence=left_sentence,
                right_sentence=right_sentence,
                connection=scoped_connection,
            )
            scoped_connection.commit()
        return

    delete_cursor = execute(
        connection,
        delete(sentences_table).where(sentences_table.c.id == sentence_id),
    )
    if delete_cursor.rowcount != 1:
        raise RuntimeError("Sentence clip failed: original sentence was not deleted")

    statement = insert(sentences_table).values(
        id=bindparam("id"),
        version_id=bindparam("version_id"),
        doc_id=bindparam("doc_id"),
        start_offset=bindparam("start_offset"),
        end_offset=bindparam("end_offset"),
        source_text=bindparam("source_text"),
        corrected_text=bindparam("corrected_text"),
    )
    execute_many(
        connection,
        statement,
        [
            _normalize_sentence_row(left_sentence),
            _normalize_sentence_row(right_sentence),
        ],
    )


def update_sentence_corrected_text(
    sentence_id: str,
    corrected_text: str,
    connection: Connection | None = None,
) -> SentenceRow:
    if connection is None:
        with connection_scope() as scoped_connection:
            sentence = update_sentence_corrected_text(
                sentence_id=sentence_id,
                corrected_text=corrected_text,
                connection=scoped_connection,
            )
            scoped_connection.commit()
            return sentence

    cursor = execute(
        connection,
        update(sentences_table)
        .where(sentences_table.c.id == sentence_id)
        .values(corrected_text=corrected_text),
    )
    if cursor.rowcount <= 0:
        raise FileNotFoundError(f"Sentence not found: {sentence_id}")

    sentence = get_sentence_by_id(sentence_id, connection=connection)
    if sentence is None:
        raise FileNotFoundError(f"Sentence not found after update: {sentence_id}")

    return sentence


def rm_sentences_by_version_id(version_id: str, connection: Connection | None = None) -> int:
    if connection is None:
        with connection_scope() as scoped_connection:
            removed = rm_sentences_by_version_id(version_id, connection=scoped_connection)
            scoped_connection.commit()
            return removed

    cursor = execute(
        connection,
        delete(sentences_table).where(sentences_table.c.version_id == version_id),
    )
    return cursor.rowcount


def _normalize_sentence_row(row: Mapping[str, int | str]) -> SentenceRow:
    return {
        "id": str(row["id"]),
        "version_id": str(row["version_id"]),
        "doc_id": str(row["doc_id"]),
        "start_offset": int(row["start_offset"]),
        "end_offset": int(row["end_offset"]),
        "source_text": str(row["source_text"]),
        "corrected_text": str(row["corrected_text"]),
    }
