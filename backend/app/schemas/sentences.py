from pydantic import BaseModel

from app.schemas.processings import ProcessingItem


class SentenceItem(BaseModel):
    id: str
    version_id: str
    doc_id: str
    start_offset: int
    end_offset: int
    source_text: str
    corrected_text: str


class SentenceSegmentationResponse(BaseModel):
    processing: ProcessingItem
    sentence_count: int
    preview: list[SentenceItem]


class SentenceCursorPage(BaseModel):
    items: list[SentenceItem]
    next_after_start_offset: int | None = None
    has_more: bool


class MergeSentenceRequest(BaseModel):
    sentence_ids: list[str]


class SentenceClipRequest(BaseModel):
    sentence_id: str
    split_offset: int


class SentenceClipResponse(BaseModel):
    items: list[SentenceItem]


class SentenceCorrectRequest(BaseModel):
    sentence_id: str
    corrected_text: str
