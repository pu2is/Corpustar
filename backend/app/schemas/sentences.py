from pydantic import BaseModel, Field


class SentenceItem(BaseModel):
    id: str
    version_id: str
    doc_id: str
    start_offset: int
    end_offset: int
    source_text: str
    corrected_text: str


class SentenceCursorPageRequest(BaseModel):
    doc_id: str
    segmentation_id: str
    split_offset: int | None = Field(default=None, ge=0)
    limit: int = Field(ge=1)


class MergeSentenceRequest(BaseModel):
    sentence_ids: list[str]


class SentenceClipRequest(BaseModel):
    sentence_id: str
    split_offset: int


class SentenceCorrectRequest(BaseModel):
    sentence_id: str
    corrected_text: str


class SentenceActionResponse(BaseModel):
    id: str
    ok: bool
    error_msg: str = ""
