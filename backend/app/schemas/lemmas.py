from pydantic import BaseModel


class LemmaTokenItem(BaseModel):
    id: str
    version_id: str
    sentence_id: str
    source_word: str
    lemma_word: str
    word_index: int
    head_index: int
    pos_tag: str
    fine_pos_tag: str
    morph: str
    dependency_relationship: str


class LemmaTokensBySentenceRequest(BaseModel):
    sentence_ids: list[str]
