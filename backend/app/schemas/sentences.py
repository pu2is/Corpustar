from pydantic import BaseModel

from app.schemas.processings import ProcessingItem


class SentenceItem(BaseModel):
    id: str
    docId: str
    processingId: str
    startOffset: int
    endOffset: int
    lemmaText: str | None
    text: str


class SentenceSegmentationResponse(BaseModel):
    processing: ProcessingItem
    sentenceCount: int
    preview: list[SentenceItem]


class SentenceSegmentationLatestResponse(BaseModel):
    processing: ProcessingItem | None = None
    sentenceCount: int
    preview: list[SentenceItem]


class SentenceCursorPage(BaseModel):
    items: list[SentenceItem]
    nextAfterStartOffset: int | None = None
    hasMore: bool


class MergeSentenceRequest(BaseModel):
    sentenceIds: list[str]


class ClipSentenceRequest(BaseModel):
    splitOffset: int
