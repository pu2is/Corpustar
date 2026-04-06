from pydantic import BaseModel, Field

from app.schemas.lemmas import LemmaTokenItem
from app.schemas.sentences import SentenceItem


class FvgCandidateItem(BaseModel):
    id: str
    sentence_id: str
    process_id: str
    algo_fvg_entry_id: str
    corrected_fvg_entry_id: str
    algo_verb_token: str
    algo_verb_index: int
    corrected_verb_token: str
    corrected_verb_index: int
    algo_noun_token: str
    algo_noun_index: int
    corrected_noun_token: str
    corrected_noun_index: int
    algo_prep_token: str
    algo_prep_index: int
    corrected_prep_token: str
    corrected_prep_index: int
    label: str
    manuelle_created: bool
    removed: bool


class SentenceFvgItem(SentenceItem):
    fvg_candidates: list[FvgCandidateItem] = Field(default_factory=list)
    lemma_tokens: list[LemmaTokenItem] = Field(default_factory=list)


class SentenceFvgCursorSchema(BaseModel):
    currentCursor: str | None = None
    nextCursor: str | None = None
    previousCursor: str | None = None


class SentenceFvgListRequest(BaseModel):
    segmentation_id: str
    cursor: str | None = None
    limit: int = Field(ge=1, default=20)


class SentenceFvgDetectedListRequest(BaseModel):
    fvg_process_id: str
    cursor: str | None = None
    limit: int = Field(ge=1, default=20)


class SentenceFvgListItem(BaseModel):
    sentences: list[SentenceFvgItem]
    cursor: SentenceFvgCursorSchema
