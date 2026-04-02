from pydantic import BaseModel, Field


class SentenceItem(BaseModel):
    id: str
    version_id: str
    doc_id: str
    start_offset: int
    end_offset: int
    source_text: str
    corrected_text: str


class ExtendedSentenceItem(SentenceItem):
    pass


class SentenceCursorPageRequest(BaseModel):
    doc_id: str
    segmentation_id: str
    cursor: str | None = None
    limit: int = Field(ge=1)


class SentenceCursorSchema(BaseModel):
    currentCursor: str | None = None
    nextCursor: str | None = None
    prevCursor: str | None = None


class SentenceDisplayResponse(BaseModel):
    prevSentence: SentenceItem | None = None
    sentences: list[ExtendedSentenceItem]
    cursor: SentenceCursorSchema
    highlight: list[str] = Field(default_factory=list)


class MergeSentenceRequest(BaseModel):
    sentence_ids: list[str]
    limit: int | None = Field(default=None, ge=1)


class SentenceClipRequest(BaseModel):
    sentence_id: str
    split_offset: int
    limit: int | None = Field(default=None, ge=1)


class SentenceCorrectRequest(BaseModel):
    sentence_id: str
    corrected_text: str
    cursor: str | None
    limit: int = Field(ge=1)


class SentenceActionResponse(BaseModel):
    id: str
    ok: bool
    error_msg: str = ""
