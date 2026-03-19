from typing import Any, TypedDict

from app.schemas.processings import ProcessingState, ProcessingType
from app.services.sentence.types import SentenceItem


class ProcessingItemDict(TypedDict):
    id: str
    docId: str
    type: ProcessingType
    state: ProcessingState
    createdAt: str
    updatedAt: str
    errorMessage: str | None
    meta: dict[str, Any] | None


class SentenceSpan(TypedDict):
    start_offset: int
    end_offset: int


class SentenceSegmentationResult(TypedDict):
    processing: ProcessingItemDict | None
    sentenceCount: int
    preview: list[SentenceItem]
