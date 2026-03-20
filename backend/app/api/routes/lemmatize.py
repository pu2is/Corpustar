from fastapi import APIRouter, HTTPException, Query

from app.core.log import get_logger, log_event
from app.schemas.lemmas import ActionResponse, LemmaCorrectRequest, LemmaItem
from app.services.lemma.edit import correct_lemma
from app.services.lemma.load import get_lemma_items

router = APIRouter()
LOGGER = get_logger(__name__)
MODULE_FILE = __file__


@router.get("/lemma/{segmentation_id}", response_model=list[LemmaItem])
def get_lemma_items_route(segmentation_id: str, start_lemma_id: str | None = Query(default=None, alias="start_lemma_id"), limit: int = Query(..., ge=1),) -> list[LemmaItem]:
    function_name = "get_lemma_items_route"
    log_event(LOGGER, stage="CALL", module_file=MODULE_FILE, function_name=function_name, 
        segmentation_id=segmentation_id, start_lemma_id=start_lemma_id, limit=limit)

    try:
        response = get_lemma_items(segmentation_id=segmentation_id, start_lemma_id=start_lemma_id, limit=limit)
        log_event(LOGGER, stage="OK", module_file=MODULE_FILE, function_name=function_name, 
            segmentation_id=segmentation_id, result=len(response))
        return response
    
    except FileNotFoundError as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE,
            function_name=function_name, segmentation_id=segmentation_id, error=str(error))
        raise HTTPException(status_code=404, detail=str(error)) from error
    
    except ValueError as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE,
            function_name=function_name, segmentation_id=segmentation_id, error=str(error))
        raise HTTPException(status_code=400, detail=str(error)) from error
    
    except Exception as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE,  function_name=function_name,
            segmentation_id=segmentation_id, error=str(error), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/lemma/correct/{lemma_id}", response_model=ActionResponse)
def correct_lemma_route(lemma_id: str, payload: LemmaCorrectRequest) -> ActionResponse:
    function_name = "correct_lemma_route"
    log_event(LOGGER, stage="CALL", module_file=MODULE_FILE,
        function_name=function_name, lemma_id=lemma_id)

    if payload.id != lemma_id:
        raise HTTPException(status_code=400, detail="Path lemma_id does not match request body")

    try:
        correct_lemma(lemma_id=lemma_id, corrected_lemma=payload.corrected_lemma)
        log_event(LOGGER, stage="OK", module_file=MODULE_FILE,
            function_name=function_name, lemma_id=lemma_id, result="updated")
        return {"succeed": True, "error_msg": None}
    
    except FileNotFoundError as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE,
            function_name=function_name, lemma_id=lemma_id, error=str(error))
        raise HTTPException(status_code=404, detail=str(error)) from error
    
    except ValueError as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE,
            function_name=function_name, lemma_id=lemma_id, error=str(error))
        raise HTTPException(status_code=400, detail=str(error)) from error
    
    except Exception as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE, function_name=function_name,
            lemma_id=lemma_id, error=str(error), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from error
