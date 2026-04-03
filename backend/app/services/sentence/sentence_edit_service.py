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
    read_sentences_before_cursor,
    read_sentences_by_version_cursor,
    read_sentences_by_version_from_cursor,
    replace_sentence_with_split,
    update_sentence_corrected_text,
)
from app.services.sentence.pagination import DEFAULT_PAGE_LIMIT, _encode_cursor, get_sentence_cursor_page
from app.services.sentence.types import ClipSentenceResult, SentenceDisplayPage, SentenceItem, SentenceRow
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


def _resolve_page_meta(
    socket_meta: dict[str, Any] | None,
) -> tuple[int, str | None]:
    page_limit = DEFAULT_PAGE_LIMIT
    requested_cursor: str | None = None

    if socket_meta is None:
        return page_limit, requested_cursor

    for candidate in (
        socket_meta.get("limit"),
        socket_meta.get("page_size"),
        socket_meta.get("pageSize"),
    ):
        if isinstance(candidate, int) and candidate > 0:
            page_limit = candidate
            break

    cursor_candidate = socket_meta.get("cursor")
    if isinstance(cursor_candidate, str):
        cursor_candidate = cursor_candidate.strip()
        requested_cursor = cursor_candidate or None

    return page_limit, requested_cursor


def _infer_cursor_from_sentence_row(
    sentence_row: SentenceRow,
    *,
    limit: int,
) -> str | None:
    if limit < 1:
        raise ValueError("limit must be greater than or equal to 1")

    doc_id = str(sentence_row["doc_id"])
    version_id = str(sentence_row["version_id"])
    sentence_start_offset = int(sentence_row["start_offset"])
    sentence_id = str(sentence_row["id"])

    previous_rows = read_sentences_before_cursor(
        doc_id=doc_id,
        version_id=version_id,
        cursor_start_offset=sentence_start_offset,
        cursor_id=sentence_id,
        limit=None,
    )
    previous_count = len(previous_rows)
    if previous_count <= 0:
        return None

    page_start_index = previous_count - (previous_count % limit)
    if page_start_index <= 0:
        return None

    rows_to_page_start = read_sentences_by_version_cursor(
        doc_id=doc_id,
        version_id=version_id,
        limit=page_start_index + 1,
    )
    if len(rows_to_page_start) <= page_start_index:
        return None

    page_start_row = rows_to_page_start[page_start_index]
    return _encode_cursor(
        {
            "start_offset": int(page_start_row["start_offset"]),
            "id": str(page_start_row["id"]),
        }
    )


def _clone_page_payload(
    page_payload: SentenceDisplayPage,
    *,
    highlight: list[str],
) -> SentenceDisplayPage:
    return {
        "prevSentence": page_payload["prevSentence"],
        "sentences": list(page_payload["sentences"]),
        "cursor": {
            "currentCursor": page_payload["cursor"]["currentCursor"],
            "nextCursor": page_payload["cursor"]["nextCursor"],
            "prevCursor": page_payload["cursor"]["prevCursor"],
        },
        "highlight": list(highlight),
    }


def _find_sentence_index(
    sentence_items: list[SentenceItem],
    sentence_id: str,
) -> int:
    for index, sentence_item in enumerate(sentence_items):
        if sentence_item["id"] == sentence_id:
            return index
    return -1


def _read_next_sentence_item(
    *,
    doc_id: str,
    version_id: str,
    sentence_item: SentenceItem,
) -> SentenceItem | None:
    rows = read_sentences_by_version_from_cursor(
        doc_id=doc_id,
        version_id=version_id,
        cursor_start_offset=int(sentence_item["start_offset"]),
        cursor_id=str(sentence_item["id"]),
        limit=2,
    )
    for row in rows:
        if str(row["id"]) != sentence_item["id"]:
            return build_sentence_item_from_row(sentence_row=row)
    return None


def _repage_from_first_sentence(
    *,
    doc_id: str,
    version_id: str,
    limit: int,
    first_sentence: SentenceItem | None,
    highlight: list[str],
) -> SentenceDisplayPage:
    first_cursor = None
    if first_sentence is not None:
        first_cursor = _encode_cursor(
            {
                "start_offset": int(first_sentence["start_offset"]),
                "id": str(first_sentence["id"]),
            }
        )

    return get_sentence_cursor_page(
        doc_id=doc_id,
        segmentation_id=version_id,
        cursor=first_cursor,
        limit=limit,
        highlight=highlight,
    )


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

    page_limit, requested_cursor = _resolve_page_meta(socket_meta)
    effective_cursor = requested_cursor
    if effective_cursor is None:
        effective_cursor = _infer_cursor_from_sentence_row(second_row, limit=page_limit)
    pre_merge_page = get_sentence_cursor_page(
        doc_id=doc_id,
        segmentation_id=str(first_row["version_id"]),
        cursor=effective_cursor,
        limit=page_limit,
        highlight=[],
    )

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

    first_sentence_id = unique_sentence_ids[0]
    second_sentence_id = unique_sentence_ids[1]
    page_payload: SentenceDisplayPage | None = None

    first_index = _find_sentence_index(pre_merge_page["sentences"], first_sentence_id)
    second_index = _find_sentence_index(pre_merge_page["sentences"], second_sentence_id)

    if first_index >= 0 and second_index == first_index + 1:
        page_payload = _clone_page_payload(pre_merge_page, highlight=[merged_id])
        old_last_sentence = page_payload["sentences"][-1] if page_payload["sentences"] else None

        page_payload["sentences"][first_index] = merged_item
        del page_payload["sentences"][second_index]

        if old_last_sentence is not None and len(page_payload["sentences"]) < page_limit:
            next_sentence_item = _read_next_sentence_item(
                doc_id=doc_id,
                version_id=version_id,
                sentence_item=old_last_sentence,
            )
            if next_sentence_item is not None:
                page_payload["sentences"].append(next_sentence_item)

        if first_index == 0:
            page_payload = _repage_from_first_sentence(
                doc_id=doc_id,
                version_id=version_id,
                limit=page_limit,
                first_sentence=page_payload["sentences"][0] if page_payload["sentences"] else None,
                highlight=[merged_id],
            )
    elif (
        pre_merge_page["prevSentence"] is not None
        and str(pre_merge_page["prevSentence"]["id"]) == first_sentence_id
        and second_index == 0
        and pre_merge_page["sentences"]
    ):
        page_payload = _clone_page_payload(pre_merge_page, highlight=[merged_id])
        page_payload["sentences"][0] = merged_item
        page_payload = _repage_from_first_sentence(
            doc_id=doc_id,
            version_id=version_id,
            limit=page_limit,
            first_sentence=page_payload["sentences"][0],
            highlight=[merged_id],
        )

    if page_payload is None:
        page_payload = get_sentence_cursor_page(
            doc_id=doc_id,
            segmentation_id=version_id,
            cursor=effective_cursor,
            limit=page_limit,
            highlight=[merged_id],
        )

    contains_merged_sentence = any(item["id"] == merged_id for item in page_payload["sentences"])
    if not contains_merged_sentence:
        page_payload = _repage_from_first_sentence(
            doc_id=doc_id,
            version_id=version_id,
            limit=page_limit,
            first_sentence=merged_item,
            highlight=[merged_id],
        )
    elif len(page_payload["sentences"]) < page_limit:
        page_payload = get_sentence_cursor_page(
            doc_id=doc_id,
            segmentation_id=version_id,
            cursor=page_payload["cursor"]["currentCursor"],
            limit=page_limit,
            highlight=[merged_id],
        )

    publish_best_effort(SENTENCE_MERGED, page_payload)
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

    page_limit, requested_cursor = _resolve_page_meta(socket_meta)
    effective_cursor = requested_cursor
    if effective_cursor is None:
        effective_cursor = _infer_cursor_from_sentence_row(sentence_row, limit=page_limit)
    pre_clip_page = get_sentence_cursor_page(
        doc_id=doc_id,
        segmentation_id=version_id,
        cursor=effective_cursor,
        limit=page_limit,
        highlight=[],
    )

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

    page_payload: SentenceDisplayPage | None = None
    clipped_index = _find_sentence_index(pre_clip_page["sentences"], sentence_id)
    if clipped_index >= 0:
        page_payload = _clone_page_payload(pre_clip_page, highlight=[left_id, right_id])
        page_payload["sentences"][clipped_index] = left_item
        page_payload["sentences"].insert(clipped_index + 1, right_item)
        if len(page_payload["sentences"]) > page_limit:
            page_payload["sentences"] = page_payload["sentences"][:page_limit]

        if clipped_index == 0:
            page_payload = _repage_from_first_sentence(
                doc_id=doc_id,
                version_id=version_id,
                limit=page_limit,
                first_sentence=page_payload["sentences"][0] if page_payload["sentences"] else None,
                highlight=[left_id, right_id],
            )

    if page_payload is None:
        page_payload = get_sentence_cursor_page(
            doc_id=doc_id,
            segmentation_id=version_id,
            cursor=effective_cursor,
            limit=page_limit,
            highlight=[left_id, right_id],
        )

    contains_left_sentence = any(item["id"] == left_id for item in page_payload["sentences"])
    if not contains_left_sentence:
        page_payload = _repage_from_first_sentence(
            doc_id=doc_id,
            version_id=version_id,
            limit=page_limit,
            first_sentence=left_item,
            highlight=[left_id, right_id],
        )
    elif len(page_payload["sentences"]) < page_limit:
        page_payload = get_sentence_cursor_page(
            doc_id=doc_id,
            segmentation_id=version_id,
            cursor=page_payload["cursor"]["currentCursor"],
            limit=page_limit,
            highlight=[left_id, right_id],
        )

    publish_best_effort(SENTENCE_CLIPPED, page_payload)
    return {"items": [left_item, right_item]}


def correct_sentence(
    sentence_id: str,
    corrected_text: str,
    *,
    socket_meta: dict[str, Any] | None = None,
) -> SentenceItem:
    normalized_text = corrected_text.strip()
    if not normalized_text:
        raise ValueError("corrected_text is required")

    existing_sentence_row = get_sentence_by_id(sentence_id)
    if existing_sentence_row is None:
        raise FileNotFoundError(f"Sentence not found: {sentence_id}")

    page_limit, requested_cursor = _resolve_page_meta(socket_meta)
    effective_cursor = requested_cursor
    if effective_cursor is None:
        effective_cursor = _infer_cursor_from_sentence_row(existing_sentence_row, limit=page_limit)
    pre_correct_page = get_sentence_cursor_page(
        doc_id=str(existing_sentence_row["doc_id"]),
        segmentation_id=str(existing_sentence_row["version_id"]),
        cursor=effective_cursor,
        limit=page_limit,
        highlight=[],
    )

    sentence_row = update_sentence_corrected_text(sentence_id, normalized_text)
    sentence_item = build_sentence_item_from_row(sentence_row)

    payload: SentenceDisplayPage | None = None
    corrected_index = _find_sentence_index(pre_correct_page["sentences"], sentence_id)
    if corrected_index >= 0:
        payload = _clone_page_payload(pre_correct_page, highlight=[sentence_id])
        payload["sentences"][corrected_index] = sentence_item

    if payload is None:
        payload = get_sentence_cursor_page(
            doc_id=sentence_item["doc_id"],
            segmentation_id=sentence_item["version_id"],
            cursor=effective_cursor,
            limit=page_limit,
            highlight=[sentence_id],
        )

    contains_corrected_sentence = any(item["id"] == sentence_id for item in payload["sentences"])
    if not contains_corrected_sentence:
        payload = _repage_from_first_sentence(
            doc_id=sentence_item["doc_id"],
            version_id=sentence_item["version_id"],
            limit=page_limit,
            first_sentence=sentence_item,
            highlight=[sentence_id],
        )
    elif len(payload["sentences"]) < page_limit:
        payload = get_sentence_cursor_page(
            doc_id=sentence_item["doc_id"],
            segmentation_id=sentence_item["version_id"],
            cursor=payload["cursor"]["currentCursor"],
            limit=page_limit,
            highlight=[sentence_id],
        )

    publish_best_effort(SENTENCE_CORRECTED, payload)
    return sentence_item
