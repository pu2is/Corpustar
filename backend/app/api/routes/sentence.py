from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.log import get_logger, log_event
from app.schemas.sentences import (
    ClipSentenceRequest,
    MergeSentenceRequest,
    SentenceCursorPage,
    SentenceItem,
)
from app.services.sentence.pagination import get_sentence_cursor_page
from app.services.sentence.sentence_edit_service import clip_sentence, merge_sentences

router = APIRouter()
LOGGER = get_logger(__name__)
MODULE_FILE = __file__


class ClipSentenceResponse(BaseModel):
    items: list[SentenceItem]


@router.get("/sentences/{doc_id}", response_model=SentenceCursorPage)
def get_document_sentences(doc_id: str, processing_id: str = Query(..., alias="processingId"),
    after_start_offset: int | None = Query(default=None, alias="afterStartOffset"), limit: int = Query(..., ge=1)) -> SentenceCursorPage:
    
    function_name = "get_document_sentences_route"
    log_event(LOGGER, stage="CALL", module_file=MODULE_FILE, function_name=function_name,
        doc_id=doc_id, processing_id=processing_id, after_start_offset=after_start_offset, limit=limit)

    try:
        response = get_sentence_cursor_page(doc_id=doc_id, processing_id=processing_id,                                    
            after_start_offset=after_start_offset, limit=limit)
        log_event(LOGGER, stage="OK", module_file=MODULE_FILE, function_name=function_name,
            doc_id=doc_id, processing_id=processing_id, result=len(response["items"]), has_more=response["hasMore"])
        return response

    except FileNotFoundError as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE, function_name=function_name,
            doc_id=doc_id, processing_id=processing_id, error=str(error))
        raise HTTPException(status_code=404, detail=str(error)) from error

    except ValueError as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE, function_name=function_name,
            doc_id=doc_id, processing_id=processing_id, error=str(error))
        raise HTTPException(status_code=400, detail=str(error)) from error

    except Exception as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE, function_name=function_name,
            doc_id=doc_id, processing_id=processing_id, error=str(error), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/sentences/merge", response_model=SentenceItem)
def merge_sentences(payload: MergeSentenceRequest) -> SentenceItem:
    function_name = "merge_sentences_route"
    log_event( LOGGER, stage="CALL", module_file=MODULE_FILE,
        function_name=function_name, sentence_ids_count=len(payload.sentenceIds))

    try:
        response = merge_sentences(payload.sentenceIds)
        log_event(LOGGER, stage="OK", module_file=MODULE_FILE,
            function_name=function_name, result=response["id"])
        return response
    
    except FileNotFoundError as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE,
            function_name=function_name, error=str(error))
        raise HTTPException(status_code=404, detail=str(error)) from error
    
    except ValueError as error:
        log_event( LOGGER, stage="ERROR", module_file=MODULE_FILE,
            function_name=function_name, error=str(error))
        raise HTTPException(status_code=400, detail=str(error)) from error
    
    except Exception as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE,
            function_name=function_name, error=str(error), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/sentences/{sentence_id}/clip", response_model=ClipSentenceResponse)
def clip_sentence(sentence_id: str, payload: ClipSentenceRequest) -> ClipSentenceResponse:
    function_name = "clip_sentence_route"
    log_event(LOGGER, stage="CALL", module_file=MODULE_FILE,
        function_name=function_name, sentence_id=sentence_id, split_offset=payload.splitOffset)

    try:
        response = clip_sentence(sentence_id=sentence_id, split_offset=payload.splitOffset)
        log_event(LOGGER, stage="OK", module_file=MODULE_FILE,
            function_name=function_name, sentence_id=sentence_id, result=len(response["items"]))
        return response
    
    except FileNotFoundError as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE,
            function_name=function_name, sentence_id=sentence_id, error=str(error))
        raise HTTPException(status_code=404, detail=str(error)) from error
    
    except ValueError as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE, function_name=function_name,
            sentence_id=sentence_id, error=str(error))
        raise HTTPException(status_code=400, detail=str(error)) from error
    
    except Exception as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE, function_name=function_name, 
            sentence_id=sentence_id, error=str(error), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from error
