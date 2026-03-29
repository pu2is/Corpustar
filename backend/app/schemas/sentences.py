from pydantic import AliasChoices, BaseModel, Field

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


class SentenceCursorPageRequest(BaseModel):
    doc_id: str = Field(validation_alias=AliasChoices("doc_id", "docId"))
    segmentation_id: str = Field(
        validation_alias=AliasChoices(
            "segmentation_id",
            "segmentationId",
            "processing_id",
            "processingId",
        )
    )
    after_start_offset: int | None = Field(
        default=None,
        ge=0,
        validation_alias=AliasChoices("after_start_offset", "afterStartOffset"),
    )
    limit: int = Field(ge=1)


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
