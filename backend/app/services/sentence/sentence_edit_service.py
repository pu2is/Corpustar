from uuid import uuid4

from app.core.document.document_utils import load_txt_by_path
from app.core.sentence.build_sentence_items import build_sentence_item
from app.infrastructure.repositories.document_repository import get_document_by_id
from app.infrastructure.repositories.sentence_repository import (get_sentence_by_id, get_sentences_by_ids,
    merge_sentences_to_one, replace_sentence_with_split)
from app.services.sentence.types import ClipSentenceResult, SentenceItem, SentenceRow
from app.socket.socket_events import SENTENCE_CLIPPED, SENTENCE_MERGED
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

    full_text = load_txt_by_path(document["textPath"])
    sorted_rows = _validate_sentence_rows_for_merge(sentence_rows, full_text)

    merged_start_offset = int(min(row["start_offset"] for row in sorted_rows))
    merged_end_offset = int(max(row["end_offset"] for row in sorted_rows))
    merged_id = str(uuid4())
    processing_id = str(sorted_rows[0]["processing_id"])

    merge_sentences_to_one(
        sentence_ids=unique_sentence_ids,
        merged_sentence={
            "id": merged_id,
            "doc_id": doc_id,
            "processing_id": processing_id,
            "start_offset": merged_start_offset,
            "end_offset": merged_end_offset,
            "source_text": full_text[merged_start_offset:merged_end_offset],
            "lemma_text": None,
        },
    )

    publish_best_effort(
        SENTENCE_MERGED,
        {
            "docId": doc_id,
            "processingId": processing_id,
            "mergedSentenceId": merged_id,
        },
    )

    return build_sentence_item(
        sentence_id=merged_id,
        doc_id=doc_id,
        processing_id=processing_id,
        start_offset=merged_start_offset,
        end_offset=merged_end_offset,
        lemma_text=None,
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

    full_text = load_txt_by_path(document["textPath"])
    original_text = full_text[start_offset:end_offset]
    left_text = full_text[start_offset:split_offset]
    right_text = full_text[split_offset:end_offset]

    if not left_text.strip() or not right_text.strip():
        raise ValueError(
            "split_offset produces an empty or whitespace-only sentence fragment."
        )

    left_id = str(uuid4())
    right_id = str(uuid4())

    # Future evolution: if we need edit history, write split output into a
    # manual_sentence_edit processing result set instead of in-place updates.
    replace_sentence_with_split(
        sentence_id=sentence_id,
        left_sentence={
            "id": left_id,
            "doc_id": doc_id,
            "processing_id": processing_id,
            "start_offset": start_offset,
            "end_offset": split_offset,
            "source_text": full_text[start_offset:split_offset],
            "lemma_text": None,
        },
        right_sentence={
            "id": right_id,
            "doc_id": doc_id,
            "processing_id": processing_id,
            "start_offset": split_offset,
            "end_offset": end_offset,
            "source_text": full_text[split_offset:end_offset],
            "lemma_text": None,
        },
    )

    left_item = build_sentence_item(
        sentence_id=left_id,
        doc_id=doc_id,
        processing_id=processing_id,
        start_offset=start_offset,
        end_offset=split_offset,
        lemma_text=None,
        full_text=full_text,
    )
    right_item = build_sentence_item(
        sentence_id=right_id,
        doc_id=doc_id,
        processing_id=processing_id,
        start_offset=split_offset,
        end_offset=end_offset,
        lemma_text=None,
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
