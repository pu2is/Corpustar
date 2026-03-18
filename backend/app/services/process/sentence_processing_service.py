from pathlib import Path
from typing import Any, TypedDict

from app.socket.socket_events import (
    PROCESSING_CREATED,
    PROCESSING_UPDATED,
    SENTENCE_LIST_REBUILT,
)
from app.socket.socket_publisher import publish_best_effort
from app.infrastructure.repositories.document_repository import get_document_by_id
from app.infrastructure.repositories.processing_repository import (
    create_processing,
    get_latest_processing_by_doc_id_and_type,
    get_processing_by_id,
    map_processing_row_to_dto,
    update_processing_state,
)
from app.infrastructure.repositories.sentence_repository import (
    bulk_insert_sentences,
    count_sentences_by_processing,
    list_sentences_by_processing_cursor,
)
from app.services.process.sentence_segmentation_service import segment_text_to_sentence_spans

SENTENCE_SEGMENTATION_PROCESSING_TYPE = "sentence_segmentation"
SEGMENTATION_PREVIEW_LIMIT = 20
MAX_CURSOR_LIMIT = 200
DEFAULT_CURSOR_LIMIT = 50
SentenceRow = dict[str, int | str | None]


class SentenceItem(TypedDict):
    id: str
    docId: str
    processingId: str
    startOffset: int
    endOffset: int
    text: str
    lemmaText: str | None


class SentenceSegmentationResult(TypedDict):
    processing: dict[str, Any] | None
    sentenceCount: int
    preview: list[SentenceItem]


class SentenceCursorPage(TypedDict):
    items: list[SentenceItem]
    nextAfterStartOffset: int | None
    hasMore: bool


def _read_document_text_by_path(text_path: str) -> str:
    resolved_text_path = Path(text_path)
    if not resolved_text_path.exists() or not resolved_text_path.is_file():
        raise FileNotFoundError(f"Document text file not found: {text_path}")
    return resolved_text_path.read_text(encoding="utf-8")


def _validate_sentence_offsets(
    sentence_id: str,
    start_offset: int,
    end_offset: int,
    full_text_length: int,
) -> None:
    if start_offset < 0:
        raise ValueError(f"Sentence {sentence_id} has negative start offset: {start_offset}")
    if end_offset <= start_offset:
        raise ValueError(
            f"Sentence {sentence_id} has invalid offsets: start={start_offset}, end={end_offset}"
        )
    if end_offset > full_text_length:
        raise ValueError(
            f"Sentence {sentence_id} offset out of range: end={end_offset}, text_length={full_text_length}"
        )


def _map_sentence_row_to_item(sentence_row: SentenceRow, full_text: str) -> SentenceItem:
    sentence_id = str(sentence_row["id"])
    start_offset = int(sentence_row["start_offset"])
    end_offset = int(sentence_row["end_offset"])
    lemma_text = sentence_row.get("lemma_text")
    _validate_sentence_offsets(
        sentence_id=sentence_id,
        start_offset=start_offset,
        end_offset=end_offset,
        full_text_length=len(full_text),
    )

    return {
        "id": sentence_id,
        "docId": str(sentence_row["doc_id"]),
        "processingId": str(sentence_row["processing_id"]),
        "startOffset": start_offset,
        "endOffset": end_offset,
        "text": (
            str(sentence_row["source_text"])
            if sentence_row.get("source_text")
            else full_text[start_offset:end_offset]
        ),
        "lemmaText": str(lemma_text) if lemma_text is not None else None,
    }


def _normalize_page_limit(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_CURSOR_LIMIT
    if limit <= 0:
        raise ValueError("limit must be greater than 0")
    return min(limit, MAX_CURSOR_LIMIT)


def _build_sentence_preview_items(
    sentence_rows: list[SentenceRow],
    full_text: str,
) -> list[SentenceItem]:
    return [
        _map_sentence_row_to_item(sentence_row=row, full_text=full_text)
        for row in sentence_rows
    ]


def _build_sentence_segmentation_result(
    processing: dict[str, Any] | None,
    sentence_count: int,
    preview_rows: list[SentenceRow],
    full_text: str,
) -> SentenceSegmentationResult:
    return {
        "processing": processing,
        "sentenceCount": sentence_count,
        "preview": _build_sentence_preview_items(
            sentence_rows=preview_rows,
            full_text=full_text,
        ),
    }


def segment_document_sentences(doc_id: str) -> SentenceSegmentationResult:
    document = get_document_by_id(doc_id)
    if document is None:
        raise FileNotFoundError(f"Document not found: {doc_id}")

    full_text = _read_document_text_by_path(document["textPath"])
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
        spans = segment_text_to_sentence_spans(full_text)
        sentence_rows = bulk_insert_sentences(
            processing_id=processing_id,
            doc_id=doc_id,
            spans=spans,
            lemma_text=None,
            full_text=full_text,
        )
        processing = update_processing_state(
            processing_id=processing_id,
            new_state="succeed",
        )
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
    publish_best_effort(
        SENTENCE_LIST_REBUILT,
        {
            "docId": doc_id,
            "processingId": processing_id,
            "sentenceCount": len(sentence_rows),
        },
    )

    preview_rows = sentence_rows[:SEGMENTATION_PREVIEW_LIMIT]
    return _build_sentence_segmentation_result(
        processing=processing_dto,
        sentence_count=len(sentence_rows),
        preview_rows=preview_rows,
        full_text=full_text,
    )


def get_sentence_cursor_page(
    doc_id: str,
    processing_id: str,
    after_start_offset: int | None,
    limit: int | None,
) -> SentenceCursorPage:
    document = get_document_by_id(doc_id)
    if document is None:
        raise FileNotFoundError(f"Document not found: {doc_id}")

    processing = get_processing_by_id(processing_id)
    if processing is None:
        raise FileNotFoundError(f"Processing not found: {processing_id}")
    if processing["doc_id"] != doc_id:
        raise ValueError(
            f"Processing {processing_id} does not belong to document {doc_id}"
        )

    normalized_limit = _normalize_page_limit(limit)
    full_text = _read_document_text_by_path(document["textPath"])

    rows = list_sentences_by_processing_cursor(
        doc_id=doc_id,
        processing_id=processing_id,
        after_start_offset=after_start_offset,
        limit=normalized_limit + 1,
    )

    has_more = len(rows) > normalized_limit
    page_rows = rows[:normalized_limit] if has_more else rows
    items = [
        _map_sentence_row_to_item(sentence_row=row, full_text=full_text)
        for row in page_rows
    ]

    next_after_start_offset = None
    if has_more and page_rows:
        next_after_start_offset = int(page_rows[-1]["start_offset"])

    return {
        "items": items,
        "nextAfterStartOffset": next_after_start_offset,
        "hasMore": has_more,
    }


def get_latest_sentence_segmentation_result(
    doc_id: str,
) -> SentenceSegmentationResult:
    document = get_document_by_id(doc_id)
    if document is None:
        raise FileNotFoundError(f"Document not found: {doc_id}")

    latest_processing = get_latest_processing_by_doc_id_and_type(
        doc_id=doc_id,
        processing_type=SENTENCE_SEGMENTATION_PROCESSING_TYPE,
        state="succeed",
    )
    if latest_processing is None:
        return _build_sentence_segmentation_result(
            processing=None,
            sentence_count=0,
            preview_rows=[],
            full_text="",
        )

    processing_id = str(latest_processing["id"])
    full_text = _read_document_text_by_path(document["textPath"])
    sentence_count = count_sentences_by_processing(
        doc_id=doc_id,
        processing_id=processing_id,
    )
    preview_rows = list_sentences_by_processing_cursor(
        doc_id=doc_id,
        processing_id=processing_id,
        after_start_offset=None,
        limit=SEGMENTATION_PREVIEW_LIMIT,
    )

    return _build_sentence_segmentation_result(
        processing=map_processing_row_to_dto(latest_processing),
        sentence_count=sentence_count,
        preview_rows=preview_rows,
        full_text=full_text,
    )
