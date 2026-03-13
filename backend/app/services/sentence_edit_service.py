from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from app.core.db import get_connection
from app.socket.socket_events import SENTENCE_CLIPPED, SENTENCE_MERGED
from app.socket.socket_publisher import publish_best_effort
from app.services.document_repository import get_document_by_id
from app.services.sentence_repository import get_sentence_by_id, get_sentences_by_ids

DOCUMENT_SENTENCES_TABLE_NAME = "document_sentences"


class SentenceItem(TypedDict):
    id: str
    docId: str
    processingId: str
    startOffset: int
    endOffset: int
    text: str


class ClipSentenceResult(TypedDict):
    items: list[SentenceItem]


def _read_document_text_by_path(text_path: str) -> str:
    resolved_text_path = Path(text_path)
    if not resolved_text_path.exists() or not resolved_text_path.is_file():
        raise FileNotFoundError(f"Document text file not found: {text_path}")
    return resolved_text_path.read_text(encoding="utf-8")


def _validate_sentence_rows_for_merge(
    sentence_rows: list[dict[str, int | str]],
    full_text: str,
) -> list[dict[str, int | str]]:
    sorted_rows = sorted(
        sentence_rows,
        key=lambda row: (int(row["start_offset"]), int(row["end_offset"])),
    )

    first_doc_id = str(sorted_rows[0]["doc_id"])
    first_processing_id = str(sorted_rows[0]["processing_id"])

    for row in sorted_rows:
        if str(row["doc_id"]) != first_doc_id:
            raise ValueError("All sentences to merge must belong to the same document.")
        if str(row["processing_id"]) != first_processing_id:
            raise ValueError("All sentences to merge must belong to the same processing.")

    for index in range(1, len(sorted_rows)):
        previous_row = sorted_rows[index - 1]
        current_row = sorted_rows[index]

        previous_end = int(previous_row["end_offset"])
        current_start = int(current_row["start_offset"])

        if current_start < previous_end:
            raise ValueError("Sentences to merge must not overlap.")

        # Future evolution: if we need audit history, write edits into a new
        # manual_sentence_edit processing result set instead of in-place updates.
        between_text = full_text[previous_end:current_start]
        if between_text.strip():
            raise ValueError(
                "Sentences to merge must be continuous in text order without non-whitespace gaps."
            )

    return sorted_rows


def _build_sentence_item(
    sentence_id: str,
    doc_id: str,
    processing_id: str,
    start_offset: int,
    end_offset: int,
    full_text: str,
) -> SentenceItem:
    if start_offset < 0:
        raise ValueError(f"Sentence {sentence_id} has negative start offset: {start_offset}")
    if end_offset <= start_offset:
        raise ValueError(
            f"Sentence {sentence_id} has invalid offsets: start={start_offset}, end={end_offset}"
        )
    if end_offset > len(full_text):
        raise ValueError(
            f"Sentence {sentence_id} offset out of range: end={end_offset}, text_length={len(full_text)}"
        )

    return {
        "id": sentence_id,
        "docId": doc_id,
        "processingId": processing_id,
        "startOffset": start_offset,
        "endOffset": end_offset,
        "text": full_text[start_offset:end_offset],
    }


def merge_sentences(sentence_ids: list[str]) -> SentenceItem:
    unique_sentence_ids = list(dict.fromkeys(sentence_ids))
    if len(unique_sentence_ids) < 2:
        raise ValueError("At least two sentence IDs are required for merge.")

    sentence_rows = get_sentences_by_ids(unique_sentence_ids)
    if len(sentence_rows) != len(unique_sentence_ids):
        raise FileNotFoundError("One or more sentences were not found.")

    doc_id = str(sentence_rows[0]["doc_id"])
    document = get_document_by_id(doc_id)
    if document is None:
        raise FileNotFoundError(f"Document not found: {doc_id}")

    full_text = _read_document_text_by_path(document["textPath"])
    sorted_rows = _validate_sentence_rows_for_merge(sentence_rows, full_text)

    merged_start_offset = int(min(row["start_offset"] for row in sorted_rows))
    merged_end_offset = int(max(row["end_offset"] for row in sorted_rows))
    merged_id = str(uuid4())
    processing_id = str(sorted_rows[0]["processing_id"])

    connection_generator = get_connection()
    connection = next(connection_generator)
    try:
        connection.execute("BEGIN")

        delete_placeholders = ", ".join("?" for _ in unique_sentence_ids)
        delete_cursor = connection.execute(
            f"""
            DELETE FROM {DOCUMENT_SENTENCES_TABLE_NAME}
            WHERE id IN ({delete_placeholders})
            """,
            tuple(unique_sentence_ids),
        )
        if delete_cursor.rowcount != len(unique_sentence_ids):
            raise RuntimeError("Sentence merge failed: expected rows were not fully deleted.")

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
                merged_id,
                doc_id,
                processing_id,
                merged_start_offset,
                merged_end_offset,
            ),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection_generator.close()

    publish_best_effort(
        SENTENCE_MERGED,
        {
            "docId": doc_id,
            "processingId": processing_id,
            "mergedSentenceId": merged_id,
        },
    )

    return _build_sentence_item(
        sentence_id=merged_id,
        doc_id=doc_id,
        processing_id=processing_id,
        start_offset=merged_start_offset,
        end_offset=merged_end_offset,
        full_text=full_text,
    )


def clip_sentence(sentence_id: str, split_offset: int) -> ClipSentenceResult:
    sentence_row = get_sentence_by_id(sentence_id)
    if sentence_row is None:
        raise FileNotFoundError(f"Sentence not found: {sentence_id}")

    doc_id = str(sentence_row["doc_id"])
    processing_id = str(sentence_row["processing_id"])
    start_offset = int(sentence_row["start_offset"])
    end_offset = int(sentence_row["end_offset"])

    if split_offset <= start_offset or split_offset >= end_offset:
        raise ValueError(
            "split_offset must be strictly between sentence start_offset and end_offset."
        )

    document = get_document_by_id(doc_id)
    if document is None:
        raise FileNotFoundError(f"Document not found: {doc_id}")

    full_text = _read_document_text_by_path(document["textPath"])
    original_text = full_text[start_offset:end_offset]
    left_text = full_text[start_offset:split_offset]
    right_text = full_text[split_offset:end_offset]

    if not left_text.strip() or not right_text.strip():
        raise ValueError(
            "split_offset produces an empty or whitespace-only sentence fragment."
        )

    left_id = str(uuid4())
    right_id = str(uuid4())

    connection_generator = get_connection()
    connection = next(connection_generator)
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

        # Future evolution: if we need edit history, write split output into a
        # manual_sentence_edit processing result set instead of in-place updates.
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
                    left_id,
                    doc_id,
                    processing_id,
                    start_offset,
                    split_offset,
                ),
                (
                    right_id,
                    doc_id,
                    processing_id,
                    split_offset,
                    end_offset,
                ),
            ],
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection_generator.close()

    left_item = _build_sentence_item(
        sentence_id=left_id,
        doc_id=doc_id,
        processing_id=processing_id,
        start_offset=start_offset,
        end_offset=split_offset,
        full_text=full_text,
    )
    right_item = _build_sentence_item(
        sentence_id=right_id,
        doc_id=doc_id,
        processing_id=processing_id,
        start_offset=split_offset,
        end_offset=end_offset,
        full_text=full_text,
    )

    if f"{left_item['text']}{right_item['text']}" != original_text:
        raise RuntimeError("Sentence clip failed: split text does not match original sentence text.")

    publish_best_effort(
        SENTENCE_CLIPPED,
        {
            "docId": doc_id,
            "processingId": processing_id,
            "sentenceId": sentence_id,
        },
    )

    return {"items": [left_item, right_item]}
