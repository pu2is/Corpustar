from typing import TypedDict


SentenceRow = dict[str, int | str]


class SentenceItem(TypedDict):
    id: str
    version_id: str
    doc_id: str
    start_offset: int
    end_offset: int
    source_text: str
    corrected_text: str


class SentenceCursorPage(TypedDict):
    items: list[SentenceItem]
    next_after_start_offset: int | None
    has_more: bool


class ClipSentenceResult(TypedDict):
    items: list[SentenceItem]
