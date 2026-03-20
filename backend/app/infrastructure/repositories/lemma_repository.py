from collections.abc import Iterable, Mapping
from sqlite3 import Row
from typing import Any

from app.infrastructure.db.connection import connection_scope

DOCUMENT_SENTENCES_TABLE_NAME = "document_sentences"
LEMMA_TABLE_NAME = "lemma"

LemmaRow = dict[str, str | None]
LemmaDto = dict[str, Any]


def _map_lemma_row(row: Row) -> LemmaRow:
    return {
        "id": row["id"],
        "doc_id": row["doc_id"],
        "segmentation_id": row["segmentation_id"],
        "sentence_id": row["sentence_id"],
        "source_text": row["source_text"],
        "lemma_text": row["lemma_text"],
        "corrected_lemma": row["corrected_lemma"],
        "fvg_result_id": row["fvg_result_id"],
    }


def map_lemma_row_to_dto(lemma_row: Mapping[str, str | None]) -> LemmaDto:
    return {
        "id": lemma_row["id"],
        "docId": lemma_row["doc_id"],
        "segmentationId": lemma_row["segmentation_id"],
        "sentenceId": lemma_row["sentence_id"],
        "sourceText": lemma_row["source_text"],
        "lemmaText": lemma_row["lemma_text"],
        "correctedLemma": lemma_row["corrected_lemma"],
        "fvgResultId": lemma_row["fvg_result_id"],
    }


def get_n_lemma_from(segmentation_id: str, start_from_id: str | None, limit: int) -> list[LemmaRow]:
    if limit <= 0:
        return []

    cursor_start_offset: int | None = None
    with connection_scope() as connection:
        if start_from_id:
            cursor_row = connection.execute(
                f"""
                SELECT ds.start_offset
                FROM {LEMMA_TABLE_NAME} AS lemma
                INNER JOIN {DOCUMENT_SENTENCES_TABLE_NAME} AS ds
                    ON ds.id = lemma.sentence_id
                WHERE lemma.id = ?
                  AND lemma.segmentation_id = ?
                LIMIT 1
                """,
                (start_from_id, segmentation_id),
            ).fetchone()
            if cursor_row is None:
                raise FileNotFoundError(
                    f"Lemma cursor not found: segmentation_id={segmentation_id}, id={start_from_id}"
                )
            cursor_start_offset = int(cursor_row["start_offset"])

        parameters: list[str | int] = [segmentation_id]
        cursor_sql = ""
        if cursor_start_offset is not None:
            cursor_sql = "AND ds.start_offset > ?"
            parameters.append(cursor_start_offset)
        parameters.append(limit)

        rows = connection.execute(
            f"""
            SELECT
                lemma.id,
                lemma.doc_id,
                lemma.segmentation_id,
                lemma.sentence_id,
                lemma.source_text,
                lemma.lemma_text,
                lemma.corrected_lemma,
                lemma.fvg_result_id
            FROM {LEMMA_TABLE_NAME} AS lemma
            INNER JOIN {DOCUMENT_SENTENCES_TABLE_NAME} AS ds
                ON ds.id = lemma.sentence_id
            WHERE lemma.segmentation_id = ?
              {cursor_sql}
            ORDER BY ds.start_offset ASC
            LIMIT ?
            """,
            tuple(parameters),
        ).fetchall()
        return [_map_lemma_row(row) for row in rows]


def modify_lemma_item(lemma_id: str, new_lemma: str) -> LemmaRow:
    with connection_scope() as connection:
        cursor = connection.execute(
            f"""
            UPDATE {LEMMA_TABLE_NAME}
            SET corrected_lemma = ?
            WHERE id = ?
            """,
            (new_lemma, lemma_id),
        )
        if cursor.rowcount <= 0:
            connection.rollback()
            raise FileNotFoundError(f"Lemma item not found: {lemma_id}")

        row = connection.execute(
            f"""
            SELECT
                id,
                doc_id,
                segmentation_id,
                sentence_id,
                source_text,
                lemma_text,
                corrected_lemma,
                fvg_result_id
            FROM {LEMMA_TABLE_NAME}
            WHERE id = ?
            """,
            (lemma_id,),
        ).fetchone()
        if row is None:
            connection.rollback()
            raise FileNotFoundError(f"Lemma item not found after update: {lemma_id}")

        connection.commit()
        return _map_lemma_row(row)


def write_lemma_items_in_batch(
    lemma_items: Iterable[Mapping[str, str | None]],
    clear_existing: bool = False,
) -> None:
    items = [dict(item) for item in lemma_items]
    if not items:
        return

    segmentation_id = str(items[0]["segmentation_id"])
    with connection_scope() as connection:
        if clear_existing:
            connection.execute(
                f"""
                UPDATE {DOCUMENT_SENTENCES_TABLE_NAME}
                SET lemma_text = NULL
                WHERE processing_id = ?
                """,
                (segmentation_id,),
            )
            connection.execute(
                f"""
                DELETE FROM {LEMMA_TABLE_NAME}
                WHERE segmentation_id = ?
                """,
                (segmentation_id,),
            )

        connection.executemany(
            f"""
            INSERT OR REPLACE INTO {LEMMA_TABLE_NAME} (
                id,
                doc_id,
                segmentation_id,
                sentence_id,
                source_text,
                lemma_text,
                corrected_lemma,
                fvg_result_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    str(item["id"]),
                    str(item["doc_id"]),
                    str(item["segmentation_id"]),
                    str(item["sentence_id"]),
                    str(item["source_text"]),
                    str(item["lemma_text"]),
                    str(item["corrected_lemma"]),
                    item["fvg_result_id"],
                )
                for item in items
            ],
        )
        connection.executemany(
            f"""
            UPDATE {DOCUMENT_SENTENCES_TABLE_NAME}
            SET lemma_text = ?
            WHERE id = ?
              AND processing_id = ?
            """,
            [
                (
                    str(item["id"]),
                    str(item["sentence_id"]),
                    str(item["segmentation_id"]),
                )
                for item in items
            ],
        )
        connection.commit()
