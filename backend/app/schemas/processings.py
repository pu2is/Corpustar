from typing import Any, Literal
from pydantic import BaseModel


ProcessingType = Literal["sentence_segmentation", "lemmatize", "fvg_detection"]
ProcessingState = Literal["running", "succeed", "failed"]


class ProcessingItem(BaseModel):
    id: str
    docId: str
    type: ProcessingType
    state: ProcessingState
    createdAt: str
    updatedAt: str
    errorMessage: str | None = None
    meta: dict[str, Any] | None = None
