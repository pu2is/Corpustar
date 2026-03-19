from app.core.document.document_utils import load_txt_by_path
from app.core.sentence.build_sentence_items import build_sentence_item_from_row
from app.infrastructure.repositories.document_repository import get_document_by_id
from app.infrastructure.repositories.processing_repository import get_processing_by_id
from app.infrastructure.repositories.sentence_repository import list_sentences_by_processing_cursor
from app.services.sentence.types import SentenceCursorPage


def _normalize_after_start_offset(after_start_offset: int | None) -> int | None:
    if after_start_offset is None:
        return None
    if after_start_offset < 0:
        raise ValueError("afterStartOffset must be greater than or equal to 0.")
    return after_start_offset


def get_sentence_cursor_page(doc_id: str, processing_id: str,
    after_start_offset: int | None, limit: int) -> SentenceCursorPage:
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

    if limit < 1:
        raise ValueError("limit must be greater than or equal to 1.")

    normalized_after_start_offset = _normalize_after_start_offset(after_start_offset)
    full_text = load_txt_by_path(document["textPath"])

    try:
        rows = list_sentences_by_processing_cursor(
            doc_id=doc_id,
            processing_id=processing_id,
            after_start_offset=normalized_after_start_offset,
            limit=limit + 1,
        )
        has_more = len(rows) > limit
        page_rows = rows[:limit]
    except Exception:
        rows = list_sentences_by_processing_cursor(
            doc_id=doc_id,
            processing_id=processing_id,
            after_start_offset=normalized_after_start_offset,
            limit=None,
        )
        has_more = False
        page_rows = rows

    items = [
        build_sentence_item_from_row(sentence_row=row, full_text=full_text)
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
