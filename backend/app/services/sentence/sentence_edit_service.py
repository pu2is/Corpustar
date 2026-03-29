from typing import Any
from uuid import uuid4

from app.core.document.document_utils import load_txt_by_path
from app.core.sentence.build_sentence_items import build_sentence_item, build_sentence_item_from_row
from app.infrastructure.db.connection import connection_scope
from app.infrastructure.repositories.documents import read_document_by_id
from app.infrastructure.repositories.sentences import (
    get_sentence_by_id,
    get_sentences_by_ids,
    merge_sentences_to_one,
    replace_sentence_with_split,
    update_sentence_corrected_text,
)
from app.services.sentence.types import ClipSentenceResult, SentenceItem, SentenceRow
from app.socket.socket_events import SENTENCE_CLIPPED, SENTENCE_CORRECTED, SENTENCE_MERGED
from app.socket.socket_publisher import publish_best_effort


def _validate_sentence_rows_for_merge(
    sentence_rows: list[SentenceRow],
    full_text: str,
) -> list[SentenceRow]:
    sorted_rows = sorted(
        sentence_rows,
        key=lambda row: (int(row["start_offset"]), int(row["end_offset"])),
    )

    first_doc_id = str(sorted_rows[0]["doc_id"])
    first_version_id = str(sorted_rows[0]["version_id"])

    for row in sorted_rows:
        if str(row["doc_id"]) != first_doc_id:
            raise ValueError("All sentences to merge must belong to the same document")
        if str(row["version_id"]) != first_version_id:
            raise ValueError("All sentences to merge must belong to the same version")

    for index in range(1, len(sorted_rows)):
        previous_row = sorted_rows[index - 1]
        current_row = sorted_rows[index]

        previous_end = int(previous_row["end_offset"])
        current_start = int(current_row["start_offset"])

        if current_start < previous_end:
            raise ValueError("Sentences to merge must not overlap")

        between_text = full_text[previous_end:current_start]
        if between_text.strip():
            raise ValueError(
                "Sentences to merge must be continuous in text order without non-whitespace gaps"
            )

    return sorted_rows


def merge_sentences(
    sentence_ids: list[str],
    *,
    socket_meta: dict[str, Any] | None = None,
) -> SentenceItem:
    unique_sentence_ids = list(dict.fromkeys(sentence_ids))
    if len(unique_sentence_ids) != 2:
        raise ValueError("Exactly two sentence IDs are required for merge")

    sentence_rows = get_sentences_by_ids(unique_sentence_ids)
    if len(sentence_rows) != len(unique_sentence_ids):
        raise FileNotFoundError("One or more sentences were not found")

    sentence_row_by_id = {str(row["id"]): row for row in sentence_rows}
    first_row = sentence_row_by_id[unique_sentence_ids[0]]
    second_row = sentence_row_by_id[unique_sentence_ids[1]]

    doc_id = str(first_row["doc_id"])
    document = read_document_by_id(doc_id)
    if document is None:
        raise FileNotFoundError(f"Document not found: {doc_id}")

    full_text = load_txt_by_path(str(document["text_path"]))
    _validate_sentence_rows_for_merge(sentence_rows, full_text)

    merged_start_offset = int(first_row["start_offset"])
    merged_end_offset = int(second_row["end_offset"])
    if merged_end_offset <= merged_start_offset:
        raise ValueError("sentence_ids must be in [previous_sentence_id, current_sentence_id] order")

    merged_id = str(uuid4())
    version_id = str(first_row["version_id"])

    source_text = full_text[merged_start_offset:merged_end_offset]

    with connection_scope() as connection:
        connection.execute("BEGIN")
        merge_sentences_to_one(
            sentence_ids=unique_sentence_ids,
            merged_sentence={
                "id": merged_id,
                "version_id": version_id,
                "doc_id": doc_id,
                "start_offset": merged_start_offset,
                "end_offset": merged_end_offset,
                "source_text": source_text,
                "corrected_text": source_text,
            },
            connection=connection,
        )
        connection.commit()

    merged_item = build_sentence_item(
        sentence_id=merged_id,
        version_id=version_id,
        doc_id=doc_id,
        start_offset=merged_start_offset,
        end_offset=merged_end_offset,
        source_text=source_text,
        corrected_text=source_text,
        full_text=full_text,
    )

    publish_best_effort(
        SENTENCE_MERGED,
        {
            "result": merged_item,
            "meta": socket_meta if socket_meta is not None else {"sentence_ids": unique_sentence_ids},
        },
    )
    return merged_item


def clip_sentence(
    sentence_id: str,
    split_offset: int,
    *,
    socket_meta: dict[str, Any] | None = None,
) -> ClipSentenceResult:
    sentence_row = get_sentence_by_id(sentence_id)
    if sentence_row is None:
        raise FileNotFoundError(f"Sentence not found: {sentence_id}")

    doc_id = str(sentence_row["doc_id"])
    version_id = str(sentence_row["version_id"])
    start_offset = int(sentence_row["start_offset"])
    end_offset = int(sentence_row["end_offset"])

    if split_offset <= start_offset or split_offset >= end_offset:
        raise ValueError("split_offset must be strictly between sentence start_offset and end_offset")

    document = read_document_by_id(doc_id)
    if document is None:
        raise FileNotFoundError(f"Document not found: {doc_id}")

    full_text = load_txt_by_path(str(document["text_path"]))

    original_text = full_text[start_offset:end_offset]
    left_text = full_text[start_offset:split_offset]
    right_text = full_text[split_offset:end_offset]

    if not left_text.strip() or not right_text.strip():
        raise ValueError("split_offset produces an empty or whitespace-only sentence fragment")

    left_id = str(uuid4())
    right_id = str(uuid4())

    with connection_scope() as connection:
        connection.execute("BEGIN")
        replace_sentence_with_split(
            sentence_id=sentence_id,
            left_sentence={
                "id": left_id,
                "version_id": version_id,
                "doc_id": doc_id,
                "start_offset": start_offset,
                "end_offset": split_offset,
                "source_text": left_text,
                "corrected_text": left_text,
            },
            right_sentence={
                "id": right_id,
                "version_id": version_id,
                "doc_id": doc_id,
                "start_offset": split_offset,
                "end_offset": end_offset,
                "source_text": right_text,
                "corrected_text": right_text,
            },
            connection=connection,
        )
        connection.commit()

    left_item = build_sentence_item(
        sentence_id=left_id,
        version_id=version_id,
        doc_id=doc_id,
        start_offset=start_offset,
        end_offset=split_offset,
        source_text=left_text,
        corrected_text=left_text,
        full_text=full_text,
    )
    right_item = build_sentence_item(
        sentence_id=right_id,
        version_id=version_id,
        doc_id=doc_id,
        start_offset=split_offset,
        end_offset=end_offset,
        source_text=right_text,
        corrected_text=right_text,
        full_text=full_text,
    )

    if f"{left_item['source_text']}{right_item['source_text']}" != original_text:
        raise RuntimeError("Sentence clip failed: split text does not match original sentence text")

    publish_best_effort(
        SENTENCE_CLIPPED,
        {
            "result": [left_item, right_item],
            "meta": (
                socket_meta
                if socket_meta is not None
                else {"sentence_id": sentence_id, "split_offset": split_offset}
            ),
        },
    )
    return {"items": [left_item, right_item]}


def correct_sentence(sentence_id: str, corrected_text: str) -> SentenceItem:
    normalized_text = corrected_text.strip()
    if not normalized_text:
        raise ValueError("corrected_text is required")

    sentence_row = update_sentence_corrected_text(sentence_id, normalized_text)
    sentence_item = build_sentence_item_from_row(sentence_row)
    publish_best_effort(SENTENCE_CORRECTED, sentence_item)
    return sentence_item
