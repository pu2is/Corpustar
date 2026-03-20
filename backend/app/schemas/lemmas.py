from pydantic import BaseModel, Field


class LemmaItem(BaseModel):
    id: str
    docId: str
    segmentationId: str
    sentenceId: str
    sourceText: str
    lemmaText: str
    correctedLemma: str
    fvgResultId: str | None = None


class LemmaCorrectRequest(BaseModel):
    id: str
    corrected_lemma: str


class LemmaProcessRequest(BaseModel):
    doc_id: str | None = None
    segmentation_id: str | None = None
    preview_length: int = Field(default=0, ge=0)


class ActionResponse(BaseModel):
    succeed: bool
    error_msg: str | None = None
