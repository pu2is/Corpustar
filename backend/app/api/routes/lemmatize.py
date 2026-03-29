from fastapi import APIRouter, HTTPException

from app.schemas.lemmas import LemmaTokenItem, LemmaTokensBySentenceRequest
from app.services.lemma.load import get_lemma_tokens_by_sentence_ids

router = APIRouter()


@router.post("/lemma", response_model=dict[str, list[LemmaTokenItem]])
def get_lemma_items_route(
    payload: LemmaTokensBySentenceRequest,
) -> dict[str, list[LemmaTokenItem]]:
    try:
        return get_lemma_tokens_by_sentence_ids(sentence_ids=payload.sentence_ids)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error
