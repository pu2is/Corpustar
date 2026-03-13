from collections.abc import Iterable, Mapping
from sqlite3 import Row
from typing import TypedDict
from uuid import uuid4

from app.core.db import get_connection

DOCUMENT_SENTENCES_TABLE_NAME = "document_sentences"


class SentenceSpan(TypedDict):
    start_offset: int
    end_offset: int


SentenceRow = dict[str, int | str]


def _map_sentence_row(row: Row) -> SentenceRow:
    return {
        "id": row["id"],
        "doc_id": row["doc_id"],
        "processing_id": row["processing_id"],
        "start_offset": row["start_offset"],
        "end_offset": row["end_offset"],
    }


def bulk_insert_sentences(
    processing_id: str,
    doc_id: str,
    spans: Iterable[Mapping[str, int]],
) -> list[SentenceRow]:
    sentences: list[SentenceRow] = []
    for span in spans:
        sentence = {
            "id": str(uuid4()),
            "doc_id": doc_id,
            "processing_id": processing_id,
            "start_offset": int(span["start_offset"]),
            "end_offset": int(span["end_offset"]),
        }
        sentences.append(sentence)

    if not sentences:
        return []

    connection_generator = get_connection()
    connection = next(connection_generator)
    try:
        connection.executemany(
            f"""
            INSERT INTO {DOCUMENT_SENTENCES_TABLE_NAME} (
                id,
                doc_id,
                processing_id,
                start_offset,
                end_offset
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    sentence["id"],
                    sentence["doc_id"],
                    sentence["processing_id"],
                    sentence["start_offset"],
                    sentence["end_offset"],
                )
                for sentence in sentences
            ],
        )
        connection.commit()
        return sentences
    finally:
        connection_generator.close()


def list_sentences_by_processing_cursor(
    doc_id: str,
    processing_id: str,
    after_start_offset: int | None,
    limit: int,
) -> list[SentenceRow]:
    if limit <= 0:
        return []

    parameters: list[int | str] = [doc_id, processing_id]
    cursor_sql = ""
    if after_start_offset is not None:
        cursor_sql = "AND start_offset > ?"
        parameters.append(after_start_offset)

    parameters.append(limit)

    connection_generator = get_connection()
    connection = next(connection_generator)
    try:
        rows = connection.execute(
            f"""
            SELECT
                id,
                doc_id,
                processing_id,
                start_offset,
                end_offset
            FROM {DOCUMENT_SENTENCES_TABLE_NAME}
            WHERE doc_id = ?
              AND processing_id = ?
              {cursor_sql}
            ORDER BY start_offset ASC
            LIMIT ?
            """,
            tuple(parameters),
        ).fetchall()
        return [_map_sentence_row(row) for row in rows]
    finally:
        connection_generator.close()


def get_sentence_by_id(sentence_id: str) -> SentenceRow | None:
    connection_generator = get_connection()
    connection = next(connection_generator)
    try:
        row = connection.execute(
            f"""
            SELECT
                id,
                doc_id,
                processing_id,
                start_offset,
                end_offset
            FROM {DOCUMENT_SENTENCES_TABLE_NAME}
            WHERE id = ?
            """,
            (sentence_id,),
        ).fetchone()
        if row is None:
            return None
        return _map_sentence_row(row)
    finally:
        connection_generator.close()


def get_sentences_by_ids(sentence_ids: list[str]) -> list[SentenceRow]:
    if not sentence_ids:
        return []

    placeholders = ", ".join("?" for _ in sentence_ids)
    connection_generator = get_connection()
    connection = next(connection_generator)
    try:
        rows = connection.execute(
            f"""
            SELECT
                id,
                doc_id,
                processing_id,
                start_offset,
                end_offset
            FROM {DOCUMENT_SENTENCES_TABLE_NAME}
            WHERE id IN ({placeholders})
            ORDER BY start_offset ASC
            """,
            tuple(sentence_ids),
        ).fetchall()
        return [_map_sentence_row(row) for row in rows]
    finally:
        connection_generator.close()


def delete_sentences_by_ids(sentence_ids: list[str]) -> int:
    if not sentence_ids:
        return 0

    placeholders = ", ".join("?" for _ in sentence_ids)
    connection_generator = get_connection()
    connection = next(connection_generator)
    try:
        cursor = connection.execute(
            f"""
            DELETE FROM {DOCUMENT_SENTENCES_TABLE_NAME}
            WHERE id IN ({placeholders})
            """,
            tuple(sentence_ids),
        )
        connection.commit()
        return cursor.rowcount
    finally:
        connection_generator.close()


def insert_sentence(
    processing_id: str,
    doc_id: str,
    start_offset: int,
    end_offset: int,
) -> SentenceRow:
    sentence = {
        "id": str(uuid4()),
        "doc_id": doc_id,
        "processing_id": processing_id,
        "start_offset": start_offset,
        "end_offset": end_offset,
    }

    connection_generator = get_connection()
    connection = next(connection_generator)
    try:
        connection.execute(
            f"""
            INSERT INTO {DOCUMENT_SENTENCES_TABLE_NAME} (
                id,
                doc_id,
                processing_id,
                start_offset,
                end_offset
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                sentence["id"],
                sentence["doc_id"],
                sentence["processing_id"],
                sentence["start_offset"],
                sentence["end_offset"],
            ),
        )
        connection.commit()
        return sentence
    finally:
        connection_generator.close()


def count_sentences_by_processing(doc_id: str, processing_id: str) -> int:
    connection_generator = get_connection()
    connection = next(connection_generator)
    try:
        row = connection.execute(
            f"""
            SELECT COUNT(*) AS count
            FROM {DOCUMENT_SENTENCES_TABLE_NAME}
            WHERE doc_id = ?
              AND processing_id = ?
            """,
            (doc_id, processing_id),
        ).fetchone()
        if row is None:
            return 0
        return int(row["count"])
    finally:
        connection_generator.close()
