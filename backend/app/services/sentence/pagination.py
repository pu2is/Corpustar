from app.core.sentence.build_sentence_items import build_sentence_item_from_row
from app.infrastructure.repositories.documents import read_document_by_id
from app.infrastructure.repositories.processings import read_process_item_by_id
from app.infrastructure.repositories.sentences import read_sentences_by_version_cursor
from app.services.sentence.types import SentenceCursorPage


def _normalize_after_start_offset(after_start_offset: int | None) -> int | None:
    if after_start_offset is None:
        return None
    if after_start_offset < 0:
        raise ValueError("after_start_offset must be greater than or equal to 0")
    return after_start_offset


def get_sentence_cursor_page(
    *,
    doc_id: str,
    segmentation_id: str,
    after_start_offset: int | None,
    limit: int,
) -> SentenceCursorPage:
    document = read_document_by_id(doc_id)
    if document is None:
        raise FileNotFoundError(f"Document not found: {doc_id}")

    processing = read_process_item_by_id(segmentation_id)
    if processing is None:
        raise FileNotFoundError(f"Process item not found: {segmentation_id}")
    if processing["doc_id"] != doc_id:
        raise ValueError(f"Process item {segmentation_id} does not belong to document {doc_id}")

    if limit < 1:
        raise ValueError("limit must be greater than or equal to 1")

    normalized_after_start_offset = _normalize_after_start_offset(after_start_offset)

    rows = read_sentences_by_version_cursor(
        doc_id=doc_id,
        version_id=segmentation_id,
        after_start_offset=normalized_after_start_offset,
        limit=limit + 1,
    )

    has_more = len(rows) > limit
    page_rows = rows[:limit]
    items = [build_sentence_item_from_row(sentence_row=row) for row in page_rows]

    next_after_start_offset = None
    if has_more and page_rows:
        next_after_start_offset = int(page_rows[-1]["start_offset"])

    return {
        "items": items,
        "next_after_start_offset": next_after_start_offset,
        "has_more": has_more,
    }
