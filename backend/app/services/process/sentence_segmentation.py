# core
from app.core.document.document_utils import load_txt_by_path
from app.core.sentence.build_sentence_items import build_sentence_item_from_row
# db
from app.infrastructure.repositories.document_repository import get_document_by_id
from app.infrastructure.repositories.processing_repository import (create_processing, map_processing_row_to_dto, update_processing_state)
from app.infrastructure.repositories.sentence_repository import bulk_insert_sentences
# types
from app.services.process.types import SentenceSegmentationResult, SentenceSpan
# socket
from app.socket.socket_events import PROCESSING_CREATED, PROCESSING_UPDATED
from app.socket.socket_publisher import publish_best_effort

SENTENCE_END_CHARS = frozenset({".", "!", "?"})
# Keep common closing quotes/brackets attached to the sentence that ends with .!?.
TRAILING_CLOSER_CHARS = frozenset(
    {
        '"',
        "'",
        ")",
        "]",
        "}",
    }
)
SENTENCE_SEGMENTATION_PROCESSING_TYPE = "sentence_segmentation"
SEGMENTATION_PREVIEW_LIMIT = 20


def _skip_leading_whitespace(text: str, start_index: int) -> int:
    index = max(start_index, 0)
    text_length = len(text)
    while index < text_length and text[index].isspace():
        index += 1
    return index


def segment_sentences(full_text: str) -> list[SentenceSpan]:
    """Split text into sentence spans using absolute offsets.

    Offsets are 0-based and end_offset is exclusive.
    """
    if full_text == "":
        return []

    text_length = len(full_text)
    sentence_start = _skip_leading_whitespace(full_text, 0)
    if sentence_start >= text_length:
        return []

    spans: list[SentenceSpan] = []
    index = sentence_start

    while index < text_length:
        char = full_text[index]
        if char in SENTENCE_END_CHARS:
            sentence_end = index + 1

            while sentence_end < text_length and full_text[sentence_end] in SENTENCE_END_CHARS:
                sentence_end += 1

            while sentence_end < text_length and full_text[sentence_end] in TRAILING_CLOSER_CHARS:
                sentence_end += 1

            if full_text[sentence_start:sentence_end].strip():
                spans.append(
                    {
                        "start_offset": sentence_start,
                        "end_offset": sentence_end,
                    }
                )

            sentence_start = _skip_leading_whitespace(full_text, sentence_end)
            index = sentence_start
            continue

        index += 1

    if sentence_start < text_length:
        sentence_end = text_length
        while sentence_end > sentence_start and full_text[sentence_end - 1].isspace():
            sentence_end -= 1

        if sentence_end > sentence_start and full_text[sentence_start:sentence_end].strip():
            spans.append(
                {
                    "start_offset": sentence_start,
                    "end_offset": sentence_end,
                }
            )

    return spans


def segment_document_sentences(doc_id: str) -> SentenceSegmentationResult:
    document = get_document_by_id(doc_id)
    if document is None:
        raise FileNotFoundError(f"Document not found: {doc_id}")

    full_text = load_txt_by_path(document["textPath"])
    processing = create_processing(
        doc_id=doc_id,
        type=SENTENCE_SEGMENTATION_PROCESSING_TYPE,
        state="running",
    )
    processing_id = str(processing["id"])
    publish_best_effort(
        PROCESSING_CREATED,
        {
            "docId": doc_id,
            "processingId": processing_id,
            "state": str(processing["state"]),
        },
    )

    try:
        spans = segment_sentences(full_text)
        sentence_rows = bulk_insert_sentences(
            processing_id=processing_id,
            doc_id=doc_id,
            spans=spans,
            lemma_text=None,
            full_text=full_text,
        )
        processing = update_processing_state(processing_id=processing_id, new_state="succeed")

    except Exception as error:
        failed_message = str(error)
        try:
            failed_processing = update_processing_state(
                processing_id=processing_id,
                new_state="failed",
                error_message=failed_message,
            )
            failed_message = str(failed_processing["error_message"] or failed_message)

        except Exception:
            # Keep the original segmentation failure for API-layer mapping.
            pass
        publish_best_effort(
            PROCESSING_UPDATED,
            {
                "docId": doc_id,
                "processingId": processing_id,
                "state": "failed",
                "errorMessage": failed_message,
            },
        )
        raise

    processing_dto = map_processing_row_to_dto(processing)
    publish_best_effort(
        PROCESSING_UPDATED,
        {
            "docId": doc_id,
            "processingId": processing_id,
            "state": str(processing_dto["state"]),
            "errorMessage": processing_dto["errorMessage"],
        },
    )

    preview_rows = sentence_rows[:SEGMENTATION_PREVIEW_LIMIT]
    return {
        "processing": processing_dto,
        "sentenceCount": len(sentence_rows),
        "preview": [
            build_sentence_item_from_row(sentence_row=row, full_text=full_text)
            for row in preview_rows
        ],
    }
