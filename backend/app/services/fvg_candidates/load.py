from collections.abc import Mapping
import base64
import json
from typing import Any

from app.core.sentence.build_lemma_items import build_lemma_token_item_from_row
from app.infrastructure.repositories.fvg_candidates import (
    get_fvg_candidate_items_by_process_id,
    get_fvg_candidate_items_by_sentence_id,
)
from app.infrastructure.repositories.lemma_tokens import read_lemma_tokens_by_sentence_ids
from app.infrastructure.repositories.processings import map_process_row_to_item, read_process_item_by_id
from app.infrastructure.repositories.sentences import get_all_sentences_by_version_id, get_sentences_by_ids
from app.services.sentence.pagination import get_sentence_cursor_page

SentenceRow = Mapping[str, int | str]
FvgCandidateRow = Mapping[str, int | str | bool]

def collect_fvg_candidates_and_sentence_by_cursor(
    *,
    segmentation_id: str,
    cursor: str | None,
    limit: int,
) -> dict[str, object]:
    doc_id = _resolve_doc_id(segmentation_id)
    sentence_page = get_sentence_cursor_page(
        doc_id=doc_id,
        segmentation_id=segmentation_id,
        cursor=cursor,
        limit=limit,
        highlight=[],
    )

    page_sentence_rows = sentence_page["sentences"]
    page_sentence_ids = [str(sentence_row["id"]) for sentence_row in page_sentence_rows]
    lemma_items_by_sentence_id = _build_lemma_items_by_sentence_ids(page_sentence_ids)

    sentences = [
        _attach_all_candidates(
            sentence_row,
            lemma_items=lemma_items_by_sentence_id.get(str(sentence_row["id"]), []),
        )
        for sentence_row in page_sentence_rows
    ]
    return {
        "sentences": sentences,
        "cursor": {
            "currentCursor": sentence_page["cursor"]["currentCursor"],
            "nextCursor": sentence_page["cursor"]["nextCursor"],
            "previousCursor": sentence_page["cursor"]["prevCursor"],
        },
    }


def collect_detected_fvg_candidates_by_cursor(
    *,
    fvg_process_id: str,
    cursor: str | None,
    limit: int,
) -> dict[str, object]:
    _, segmentation_id = _resolve_fvg_process_scope(fvg_process_id)

    candidate_rows = [
        row
        for row in get_fvg_candidate_items_by_process_id(fvg_process_id)
        if not bool(row.get("removed", False))
    ]
    if not candidate_rows:
        return _empty_page()

    candidate_by_sentence: dict[str, list[FvgCandidateRow]] = {}
    for row in candidate_rows:
        sentence_id = str(row["sentence_id"])
        candidate_by_sentence.setdefault(sentence_id, []).append(row)

    sentence_ids = list(candidate_by_sentence.keys())
    sentence_rows = [
        row
        for row in get_sentences_by_ids(sentence_ids)
        if str(row["version_id"]) == segmentation_id
    ]
    ordered_rows = _sort_sentence_rows(sentence_rows)
    paged_rows, cursor_payload = _slice_sentence_rows(
        rows=ordered_rows,
        cursor=cursor,
        limit=limit,
        mode="detected",
    )

    paged_sentence_ids = [str(sentence_row["id"]) for sentence_row in paged_rows]
    lemma_items_by_sentence_id = _build_lemma_items_by_sentence_ids(paged_sentence_ids)

    sentences = [
        _build_sentence_item(
            sentence_row,
            fvg_candidates=[
                _normalize_candidate(candidate_row)
                for candidate_row in candidate_by_sentence.get(str(sentence_row["id"]), [])
            ],
            lemma_tokens=lemma_items_by_sentence_id.get(str(sentence_row["id"]), []),
        )
        for sentence_row in paged_rows
    ]
    return {"sentences": sentences, "cursor": cursor_payload}


def collect_undetected_fvg_candidates_by_cursor(
    *,
    fvg_process_id: str,
    cursor: str | None,
    limit: int,
) -> dict[str, object]:
    _, segmentation_id = _resolve_fvg_process_scope(fvg_process_id)

    detected_sentence_ids = {
        str(row["sentence_id"])
        for row in get_fvg_candidate_items_by_process_id(fvg_process_id)
        if not bool(row.get("removed", False))
    }

    all_sentence_rows = list(get_all_sentences_by_version_id(segmentation_id))
    undetected_rows = [
        row for row in all_sentence_rows if str(row["id"]) not in detected_sentence_ids
    ]
    ordered_rows = _sort_sentence_rows(undetected_rows)
    paged_rows, cursor_payload = _slice_sentence_rows(
        rows=ordered_rows,
        cursor=cursor,
        limit=limit,
        mode="undetected",
    )

    paged_sentence_ids = [str(sentence_row["id"]) for sentence_row in paged_rows]
    lemma_items_by_sentence_id = _build_lemma_items_by_sentence_ids(paged_sentence_ids)

    sentences = [
        _build_sentence_item(
            sentence_row,
            fvg_candidates=[],
            lemma_tokens=lemma_items_by_sentence_id.get(str(sentence_row["id"]), []),
        )
        for sentence_row in paged_rows
    ]
    return {"sentences": sentences, "cursor": cursor_payload}


def _resolve_doc_id(segmentation_id: str) -> str:
    process_row = read_process_item_by_id(segmentation_id)
    if process_row is None:
        raise FileNotFoundError(f"Process item not found: {segmentation_id}")
    if process_row["type"] != "sentence_segmentation":
        raise ValueError(f"Process item is not sentence_segmentation: {segmentation_id}")

    doc_id = process_row["doc_id"]
    if doc_id is None or not str(doc_id).strip():
        raise ValueError(f"Process item {segmentation_id} has no document")
    return str(doc_id)


def _resolve_fvg_process_scope(fvg_process_id: str) -> tuple[str, str]:
    process_row = read_process_item_by_id(fvg_process_id)
    if process_row is None:
        raise FileNotFoundError(f"Process item not found: {fvg_process_id}")
    if process_row["type"] != "fvg":
        raise ValueError(f"Process item is not fvg: {fvg_process_id}")

    doc_id = process_row["doc_id"]
    if doc_id is None or not str(doc_id).strip():
        raise ValueError(f"Process item {fvg_process_id} has no document")

    process_item = map_process_row_to_item(process_row)
    meta = process_item.get("meta")
    segmentation_id = _extract_segmentation_id(meta)
    if segmentation_id is None:
        fallback = str(process_row["parent_id"]).strip()
        segmentation_id = fallback if fallback else None

    if segmentation_id is None:
        raise ValueError(f"Process item {fvg_process_id} has no segmentation_id")
    return str(doc_id), segmentation_id


def _extract_segmentation_id(meta: Any) -> str | None:
    if not isinstance(meta, dict):
        return None
    value = meta.get("segmentation_id")
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            return stripped
    return None


def _sort_sentence_rows(rows: list[SentenceRow]) -> list[SentenceRow]:
    return sorted(rows, key=lambda row: (int(row["start_offset"]), str(row["id"])))


def _slice_sentence_rows(
    *,
    rows: list[SentenceRow],
    cursor: str | None,
    limit: int,
    mode: str,
) -> tuple[list[SentenceRow], dict[str, str | None]]:
    if not rows:
        return [], _empty_cursor()

    start_key = _decode_mode_cursor(cursor, expected_mode=mode)
    start_index = 0
    if start_key is not None:
        for index, row in enumerate(rows):
            row_key = (int(row["start_offset"]), str(row["id"]))
            if row_key >= (start_key["start_offset"], start_key["id"]):
                start_index = index
                break
        else:
            start_index = len(rows)

    page_rows = rows[start_index : start_index + limit]
    if not page_rows:
        return [], _empty_cursor()

    current_key = {
        "start_offset": int(page_rows[0]["start_offset"]),
        "id": str(page_rows[0]["id"]),
    }

    next_cursor: str | None = None
    if start_index + limit < len(rows):
        next_key_row = rows[start_index + limit]
        next_cursor = _encode_mode_cursor(
            {
                "start_offset": int(next_key_row["start_offset"]),
                "id": str(next_key_row["id"]),
            },
            mode=mode,
        )

    previous_cursor: str | None = None
    if start_index > 0:
        previous_start_index = max(0, start_index - limit)
        previous_key_row = rows[previous_start_index]
        previous_cursor = _encode_mode_cursor(
            {
                "start_offset": int(previous_key_row["start_offset"]),
                "id": str(previous_key_row["id"]),
            },
            mode=mode,
        )

    return (
        page_rows,
        {
            "currentCursor": _encode_mode_cursor(current_key, mode=mode),
            "nextCursor": next_cursor,
            "previousCursor": previous_cursor,
        },
    )


def _encode_mode_cursor(cursor_key: dict[str, int | str], *, mode: str) -> str:
    raw = json.dumps(
        {
            "mode": mode,
            "start_offset": int(cursor_key["start_offset"]),
            "id": str(cursor_key["id"]),
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8").rstrip("=")


def _decode_mode_cursor(
    cursor: str | None,
    *,
    expected_mode: str,
) -> dict[str, int | str] | None:
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

    mode = payload.get("mode")
    start_offset = payload.get("start_offset")
    sentence_id = payload.get("id")
    if mode != expected_mode:
        raise ValueError("Invalid cursor.mode")
    if not isinstance(start_offset, int) or start_offset < 0:
        raise ValueError("Invalid cursor.start_offset")
    if not isinstance(sentence_id, str) or not sentence_id:
        raise ValueError("Invalid cursor.id")
    return {"start_offset": start_offset, "id": sentence_id}


def _build_sentence_item(
    sentence_row: SentenceRow,
    *,
    fvg_candidates: list[dict[str, int | str | bool]],
    lemma_tokens: list[dict[str, int | str]],
) -> dict[str, object]:
    return {
        "id": str(sentence_row["id"]),
        "version_id": str(sentence_row["version_id"]),
        "doc_id": str(sentence_row["doc_id"]),
        "start_offset": int(sentence_row["start_offset"]),
        "end_offset": int(sentence_row["end_offset"]),
        "source_text": str(sentence_row["source_text"]),
        "corrected_text": str(sentence_row["corrected_text"]),
        "fvg_candidates": fvg_candidates,
        "lemma_tokens": lemma_tokens,
    }


def _attach_all_candidates(
    sentence_row: SentenceRow,
    *,
    lemma_items: list[dict[str, int | str]],
) -> dict[str, object]:
    sentence_id = str(sentence_row["id"])
    candidate_rows = get_fvg_candidate_items_by_sentence_id(sentence_id)
    visible_candidates = [row for row in candidate_rows if not bool(row.get("removed", False))]
    return _build_sentence_item(
        sentence_row,
        fvg_candidates=[_normalize_candidate(candidate_row) for candidate_row in visible_candidates],
        lemma_tokens=lemma_items,
    )


def _build_lemma_items_by_sentence_ids(sentence_ids: list[str]) -> dict[str, list[dict[str, int | str]]]:
    if not sentence_ids:
        return {}

    rows_by_sentence_id = read_lemma_tokens_by_sentence_ids(sentence_ids)
    result: dict[str, list[dict[str, int | str]]] = {}
    for sentence_id in sentence_ids:
        lemma_rows = rows_by_sentence_id.get(sentence_id, [])
        result[sentence_id] = [build_lemma_token_item_from_row(row) for row in lemma_rows]
    return result


def _normalize_candidate(candidate_row: FvgCandidateRow) -> dict[str, int | str | bool]:
    return {
        "id": str(candidate_row["id"]),
        "sentence_id": str(candidate_row["sentence_id"]),
        "process_id": str(candidate_row["process_id"]),
        "algo_fvg_entry_id": str(candidate_row["algo_fvg_entry_id"]),
        "corrected_fvg_entry_id": str(candidate_row["corrected_fvg_entry_id"]),
        "algo_verb_token": str(candidate_row["algo_verb_token"]),
        "algo_verb_index": int(candidate_row["algo_verb_index"]),
        "corrected_verb_token": str(candidate_row["corrected_verb_token"]),
        "corrected_verb_index": int(candidate_row["corrected_verb_index"]),
        "algo_noun_token": str(candidate_row["algo_noun_token"]),
        "algo_noun_index": int(candidate_row["algo_noun_index"]),
        "corrected_noun_token": str(candidate_row["corrected_noun_token"]),
        "corrected_noun_index": int(candidate_row["corrected_noun_index"]),
        "algo_prep_token": str(candidate_row["algo_prep_token"]),
        "algo_prep_index": int(candidate_row["algo_prep_index"]),
        "corrected_prep_token": str(candidate_row["corrected_prep_token"]),
        "corrected_prep_index": int(candidate_row["corrected_prep_index"]),
        "label": str(candidate_row["label"]),
        "manuelle_created": bool(candidate_row["manuelle_created"]),
        "removed": bool(candidate_row["removed"]),
    }


def _empty_cursor() -> dict[str, None]:
    return {
        "currentCursor": None,
        "nextCursor": None,
        "previousCursor": None,
    }


def _empty_page() -> dict[str, object]:
    return {
        "sentences": [],
        "cursor": _empty_cursor(),
    }
