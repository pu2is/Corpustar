from typing import Any, Literal

from pydantic import BaseModel, Field


ProcessingType = Literal["sentence_segmentation", "lemma", "fvg", "import_rule"]
ProcessingState = Literal["running", "succeed", "failed"]


class ProcessingItem(BaseModel):
    id: str
    parent_id: str
    doc_id: str | None = None
    type: ProcessingType
    state: ProcessingState
    created_at: str
    updated_at: str
    error_message: str | None = None
    meta_json: str | None = None
    meta: dict[str, Any] | None = None


class SentenceSegmentationProcessRequest(BaseModel):
    doc_id: str
    preview_length: int = Field(default=0, ge=0)


class LemmatizeProcessRequest(BaseModel):
    segmentation_id: str


class ImportRuleProcessRequest(BaseModel):
    path: str
    type: str = "fvg"


class ProcessActionResponse(BaseModel):
    id: str
    ok: bool
    error_msg: str = ""


class ImportRuleActionResponse(BaseModel):
    ok: bool
    error_msg: str = ""
