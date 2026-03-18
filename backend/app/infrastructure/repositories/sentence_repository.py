from collections.abc import Iterable, Mapping
from sqlite3 import Row
from typing import TypedDict
from uuid import uuid4

from app.infrastructure.db.connection import connection_scope

DOCUMENT_SENTENCES_TABLE_NAME = "document_sentences"


class SentenceSpan(TypedDict):
    start_offset: int
    end_offset: int


SentenceRow = dict[str, int | str | None]


def _map_sentence_row(row: Row) -> SentenceRow:
    return {
        "id": row["id"],
        "doc_id": row["doc_id"],
        "processing_id": row["processing_id"],
        "start_offset": row["start_offset"],
        "end_offset": row["end_offset"],
        "lemma_text": row["lemma_text"],
    }


def bulk_insert_sentences(
    processing_id: str,
    doc_id: str,
    spans: Iterable[Mapping[str, int]],
    lemma_text: str | None,
) -> list[SentenceRow]:
    sentences: list[SentenceRow] = []
    for span in spans:
        sentence = {
            "id": str(uuid4()),
            "doc_id": doc_id,
            "processing_id": processing_id,
            "start_offset": int(span["start_offset"]),
            "end_offset": int(span["end_offset"]),
            "lemma_text": lemma_text,
        }
        sentences.append(sentence)

    if not sentences:
        return []

    with connection_scope() as connection:
        connection.executemany(
            f"""
            INSERT INTO {DOCUMENT_SENTENCES_TABLE_NAME} (
                id,
                doc_id,
                processing_id,
                start_offset,
                end_offset,
                lemma_text
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    sentence["id"],
                    sentence["doc_id"],
                    sentence["processing_id"],
                    sentence["start_offset"],
                    sentence["end_offset"],
                    sentence["lemma_text"],
                )
                for sentence in sentences
            ],
        )
        connection.commit()
        return sentences


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

    with connection_scope() as connection:
        rows = connection.execute(
            f"""
            SELECT
                id,
                doc_id,
                processing_id,
                start_offset,
                end_offset,
                lemma_text
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


def get_sentence_by_id(sentence_id: str) -> SentenceRow | None:
    with connection_scope() as connection:
        row = connection.execute(
            f"""
            SELECT
                id,
                doc_id,
                processing_id,
                start_offset,
                end_offset,
                lemma_text
            FROM {DOCUMENT_SENTENCES_TABLE_NAME}
            WHERE id = ?
            """,
            (sentence_id,),
        ).fetchone()
        if row is None:
            return None
        return _map_sentence_row(row)


def get_sentences_by_ids(sentence_ids: list[str]) -> list[SentenceRow]:
    if not sentence_ids:
        return []

    placeholders = ", ".join("?" for _ in sentence_ids)
    with connection_scope() as connection:
        rows = connection.execute(
            f"""
            SELECT
                id,
                doc_id,
                processing_id,
                start_offset,
                end_offset,
                lemma_text
            FROM {DOCUMENT_SENTENCES_TABLE_NAME}
            WHERE id IN ({placeholders})
            ORDER BY start_offset ASC
            """,
            tuple(sentence_ids),
        ).fetchall()
        return [_map_sentence_row(row) for row in rows]


def delete_sentences_by_ids(sentence_ids: list[str]) -> int:
    if not sentence_ids:
        return 0

    placeholders = ", ".join("?" for _ in sentence_ids)
    with connection_scope() as connection:
        cursor = connection.execute(
            f"""
            DELETE FROM {DOCUMENT_SENTENCES_TABLE_NAME}
            WHERE id IN ({placeholders})
            """,
            tuple(sentence_ids),
        )
        connection.commit()
        return cursor.rowcount


def insert_sentence(
    processing_id: str,
    doc_id: str,
    start_offset: int,
    end_offset: int,
    lemma_text: str | None = None,
) -> SentenceRow:
    sentence = {
        "id": str(uuid4()),
        "doc_id": doc_id,
        "processing_id": processing_id,
        "start_offset": start_offset,
        "end_offset": end_offset,
        "lemma_text": lemma_text,
    }

    with connection_scope() as connection:
        connection.execute(
            f"""
            INSERT INTO {DOCUMENT_SENTENCES_TABLE_NAME} (
                id,
                doc_id,
                processing_id,
                start_offset,
                end_offset,
                lemma_text
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                sentence["id"],
                sentence["doc_id"],
                sentence["processing_id"],
                sentence["start_offset"],
                sentence["end_offset"],
                sentence["lemma_text"],
            ),
        )
        connection.commit()
        return sentence


def merge_sentences_to_one(
    sentence_ids: list[str],
    merged_sentence: SentenceRow,
) -> None:
    if not sentence_ids:
        raise ValueError("sentence_ids is required")

    placeholders = ", ".join("?" for _ in sentence_ids)
    with connection_scope() as connection:
        try:
            connection.execute("BEGIN")
            delete_cursor = connection.execute(
                f"""
                DELETE FROM {DOCUMENT_SENTENCES_TABLE_NAME}
                WHERE id IN ({placeholders})
                """,
                tuple(sentence_ids),
            )
            if delete_cursor.rowcount != len(sentence_ids):
                raise RuntimeError("Sentence merge failed: expected rows were not fully deleted.")

            connection.execute(
                f"""
                INSERT INTO {DOCUMENT_SENTENCES_TABLE_NAME} (
                    id,
                    doc_id,
                    processing_id,
                    start_offset,
                    end_offset,
                    lemma_text
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(merged_sentence["id"]),
                    str(merged_sentence["doc_id"]),
                    str(merged_sentence["processing_id"]),
                    int(merged_sentence["start_offset"]),
                    int(merged_sentence["end_offset"]),
                    merged_sentence["lemma_text"],
                ),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def replace_sentence_with_split(
    sentence_id: str,
    left_sentence: SentenceRow,
    right_sentence: SentenceRow,
) -> None:
    with connection_scope() as connection:
        try:
            connection.execute("BEGIN")
            delete_cursor = connection.execute(
                f"""
                DELETE FROM {DOCUMENT_SENTENCES_TABLE_NAME}
                WHERE id = ?
                """,
                (sentence_id,),
            )
            if delete_cursor.rowcount != 1:
                raise RuntimeError("Sentence clip failed: original sentence was not deleted.")

            connection.executemany(
                f"""
                INSERT INTO {DOCUMENT_SENTENCES_TABLE_NAME} (
                    id,
                    doc_id,
                    processing_id,
                    start_offset,
                    end_offset,
                    lemma_text
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        str(left_sentence["id"]),
                        str(left_sentence["doc_id"]),
                        str(left_sentence["processing_id"]),
                        int(left_sentence["start_offset"]),
                        int(left_sentence["end_offset"]),
                        left_sentence["lemma_text"],
                    ),
                    (
                        str(right_sentence["id"]),
                        str(right_sentence["doc_id"]),
                        str(right_sentence["processing_id"]),
                        int(right_sentence["start_offset"]),
                        int(right_sentence["end_offset"]),
                        right_sentence["lemma_text"],
                    ),
                ],
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def count_sentences_by_processing(doc_id: str, processing_id: str) -> int:
    with connection_scope() as connection:
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
