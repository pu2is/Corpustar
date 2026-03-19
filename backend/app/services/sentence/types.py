from typing import TypedDict


SentenceRow = dict[str, int | str | None]


class SentenceItem(TypedDict):
    id: str
    docId: str
    processingId: str
    startOffset: int
    endOffset: int
    text: str
    lemmaText: str | None


class SentenceCursorPage(TypedDict):
    items: list[SentenceItem]
    nextAfterStartOffset: int | None
    hasMore: bool


class ClipSentenceResult(TypedDict):
    items: list[SentenceItem]
