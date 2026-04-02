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


class ExtendedSentenceItem(SentenceItem):
    pass


class SentenceCursorKey(TypedDict):
    start_offset: int
    id: str


class SentenceCursorState(TypedDict):
    currentCursor: str | None
    nextCursor: str | None
    prevCursor: str | None


class SentenceDisplayPage(TypedDict):
    prevSentence: SentenceItem | None
    sentences: list[ExtendedSentenceItem]
    cursor: SentenceCursorState
    highlight: list[str]


class ClipSentenceResult(TypedDict):
    items: list[SentenceItem]
