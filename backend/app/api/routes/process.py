from fastapi import APIRouter, HTTPException
# log
from app.core.log import get_logger, log_event
# schemas
from app.schemas.lemmas import ActionResponse, LemmaProcessRequest
from app.schemas.processings import ProcessingItem
from app.schemas.sentences import SentenceSegmentationResponse
# services
from app.services.process.process_query_service import list_processing_items
from app.services.process.sentence_lemmatization import lemma_batch_io
from app.services.process.sentence_segmentation import segment_document_sentences

router = APIRouter()
LOGGER = get_logger(__name__)
MODULE_FILE = __file__


@router.get("/processes", response_model=list[ProcessingItem])
def get_processes_route() -> list[ProcessingItem]:
    function_name = "get_processes_route"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
    )

    try:
        processings = list_processing_items()
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            result=len(processings),
        )
        return processings
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            error=str(error),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/process/sentence_segmentation/{doc_id}", response_model=SentenceSegmentationResponse)
def segment_document_sentences_route(doc_id: str, preview_length: int) -> SentenceSegmentationResponse:
    function_name = "segment_document_sentences_route"
    log_event(LOGGER, stage="CALL", module_file=MODULE_FILE,
        function_name=function_name, doc_id=doc_id)

    try:
        response = segment_document_sentences(doc_id, preview_length)
        log_event(LOGGER, stage="OK", module_file=MODULE_FILE, function_name=function_name,
            doc_id=doc_id, processing_id=response["processing"]["id"], sentence_count=response["sentenceCount"])
        return response
    
    except FileNotFoundError as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE,
            function_name=function_name, doc_id=doc_id, error=str(error))
        raise HTTPException(status_code=404, detail=str(error)) from error
    
    except ValueError as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE,
            function_name=function_name, doc_id=doc_id, error=str(error))
        raise HTTPException(status_code=400, detail=str(error)) from error
    
    except Exception as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE, function_name=function_name,
            doc_id=doc_id, error=str(error), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/process/lemmatize/{segmentation_id}", response_model=ActionResponse)
def lemmatize_sentences_route(segmentation_id: str, payload: LemmaProcessRequest) -> ActionResponse:
    function_name = "lemmatize_sentences_route"
    log_event(LOGGER, stage="CALL", module_file=MODULE_FILE, function_name=function_name,
        segmentation_id=segmentation_id, preview_length=payload.preview_length)

    if payload.segmentation_id and payload.segmentation_id != segmentation_id:
        raise HTTPException(status_code=400, detail="Path segmentation_id does not match request body")

    try:
        lemma_batch_io(segmentation_id=segmentation_id, preview_length=payload.preview_length)
        log_event(LOGGER, stage="OK", module_file=MODULE_FILE, function_name=function_name,
            segmentation_id=segmentation_id, result="started_and_completed")
        return {"succeed": True, "error_msg": None}
    
    except FileNotFoundError as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE, function_name=function_name,
            segmentation_id=segmentation_id, error=str(error))
        raise HTTPException(status_code=404, detail=str(error)) from error
    
    except ValueError as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE, function_name=function_name,
            segmentation_id=segmentation_id, error=str(error))
        raise HTTPException(status_code=400, detail=str(error)) from error
    
    except Exception as error:
        log_event(LOGGER, stage="ERROR", module_file=MODULE_FILE, function_name=function_name,
            segmentation_id=segmentation_id, error=str(error), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from error
