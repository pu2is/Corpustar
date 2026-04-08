from fastapi import APIRouter, HTTPException

from app.schemas.lemmas import LemmaTokenItem, LemmaTokensBySentenceRequest, UpdateLemmaTokenRequest
from app.services.lemma.load import get_lemma_tokens_by_sentence_ids
from app.services.lemma.edit import edit_lemma_token

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


@router.patch("/lemma/{lemma_id}", response_model=LemmaTokenItem)
def update_lemma_token_route(
    lemma_id: str,
    payload: UpdateLemmaTokenRequest,
) -> LemmaTokenItem:
    try:
        return edit_lemma_token(lemma_id, payload.lemma_word, payload.pos_tag)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error

