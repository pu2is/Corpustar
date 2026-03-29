from typing import Any, TypedDict


class ProcessingItemDict(TypedDict):
    id: str
    parent_id: str
    doc_id: str | None
    type: str
    state: str
    created_at: str
    updated_at: str
    error_message: str | None
    meta_json: str | None
    meta: dict[str, Any] | None


class SentenceSpan(TypedDict):
    start_offset: int
    end_offset: int


class SentenceSegmentationResult(TypedDict):
    processing: ProcessingItemDict
    sentence_count: int
    preview: list[dict[str, Any]]
