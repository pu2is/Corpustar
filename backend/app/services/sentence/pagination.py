import base64
import json

from app.core.sentence.build_sentence_items import build_sentence_item_from_row
from app.infrastructure.repositories.documents import read_document_by_id
from app.infrastructure.repositories.processings import read_process_item_by_id
from app.infrastructure.repositories.sentences import (
    get_sentence_by_id,
    read_sentences_before_cursor,
    read_sentences_by_version_cursor,
    read_sentences_by_version_from_cursor,
)
from app.services.sentence.types import SentenceCursorKey, SentenceDisplayPage

DEFAULT_PAGE_LIMIT = 20


def _encode_cursor(cursor: SentenceCursorKey | None) -> str | None:
    if cursor is None:
        return None

    raw = json.dumps(
        {
            "start_offset": int(cursor["start_offset"]),
            "id": str(cursor["id"]),
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8").rstrip("=")


def _decode_cursor(cursor: str | None) -> SentenceCursorKey | None:
    if cursor is None:
        return None

    stripped_cursor = cursor.strip()
    if not stripped_cursor:
        return None

    padding = "=" * (-len(stripped_cursor) % 4)
    try:
        decoded = base64.urlsafe_b64decode((stripped_cursor + padding).encode("utf-8")).decode("utf-8")
        payload = json.loads(decoded)
    except Exception as error:
        raise ValueError("Invalid cursor") from error

    start_offset = payload.get("start_offset")
    sentence_id = payload.get("id")
    if not isinstance(start_offset, int) or start_offset < 0:
        raise ValueError("Invalid cursor.start_offset")
    if not isinstance(sentence_id, str) or not sentence_id:
        raise ValueError("Invalid cursor.id")

    return {"start_offset": start_offset, "id": sentence_id}


def get_sentence_cursor_page(
    *,
    doc_id: str,
    segmentation_id: str,
    limit: int,
    cursor: str | None = None,
    highlight: list[str] | None = None,
    focus_sentence_id: str | None = None,
) -> SentenceDisplayPage:
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

    normalized_highlight = [item for item in (highlight or []) if item]

    page_start_cursor_key = _decode_cursor(cursor)
    if focus_sentence_id:
        focus_row = get_sentence_by_id(focus_sentence_id)
        if focus_row is not None:
            if str(focus_row["doc_id"]) != doc_id:
                raise ValueError(f"Sentence {focus_sentence_id} does not belong to document {doc_id}")
            if str(focus_row["version_id"]) != segmentation_id:
                raise ValueError(
                    f"Sentence {focus_sentence_id} does not belong to version {segmentation_id}"
                )

            focus_start_offset = int(focus_row["start_offset"])
            focus_id = str(focus_row["id"])
            page_start_cursor_key = {"start_offset": focus_start_offset, "id": focus_id}

            if limit > 1:
                before_rows = read_sentences_before_cursor(
                    doc_id=doc_id,
                    version_id=segmentation_id,
                    cursor_start_offset=focus_start_offset,
                    cursor_id=focus_id,
                    limit=limit - 1,
                )
                if before_rows:
                    page_start_cursor_key = {
                        "start_offset": int(before_rows[-1]["start_offset"]),
                        "id": str(before_rows[-1]["id"]),
                    }

    if page_start_cursor_key is None:
        rows = read_sentences_by_version_cursor(
            doc_id=doc_id,
            version_id=segmentation_id,
            limit=limit + 1,
        )
    else:
        rows = read_sentences_by_version_from_cursor(
            doc_id=doc_id,
            version_id=segmentation_id,
            cursor_start_offset=page_start_cursor_key["start_offset"],
            cursor_id=page_start_cursor_key["id"],
            limit=limit + 1,
        )

    page_rows = rows[:limit]
    sentences = [build_sentence_item_from_row(sentence_row=row) for row in page_rows]

    if not sentences:
        return {
            "prevSentence": None,
            "sentences": [],
            "cursor": {
                "currentCursor": None,
                "nextCursor": None,
                "prevCursor": None,
            },
            "highlight": normalized_highlight,
        }

    first_sentence = sentences[0]
    first_key = {
        "start_offset": int(first_sentence["start_offset"]),
        "id": str(first_sentence["id"]),
    }

    previous_rows = read_sentences_before_cursor(
        doc_id=doc_id,
        version_id=segmentation_id,
        cursor_start_offset=first_key["start_offset"],
        cursor_id=first_key["id"],
        limit=limit,
    )
    prev_sentence = build_sentence_item_from_row(previous_rows[0]) if previous_rows else None
    prev_cursor = (
        _encode_cursor(
            {
                "start_offset": int(previous_rows[-1]["start_offset"]),
                "id": str(previous_rows[-1]["id"]),
            }
        )
        if previous_rows
        else None
    )
    next_cursor = (
        _encode_cursor(
            {
                "start_offset": int(rows[limit]["start_offset"]),
                "id": str(rows[limit]["id"]),
            }
        )
        if len(rows) > limit
        else None
    )

    return {
        "prevSentence": prev_sentence,
        "sentences": sentences,
        "cursor": {
            "currentCursor": _encode_cursor(first_key),
            "nextCursor": next_cursor,
            "prevCursor": prev_cursor,
        },
        "highlight": normalized_highlight,
    }

