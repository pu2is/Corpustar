from fastapi import APIRouter, HTTPException, Query

from app.core.log import get_logger, log_event
from app.schemas.processings import ProcessingItem
from app.schemas.sentences import (
    SentenceCursorPage,
    SentenceSegmentationLatestResponse,
    SentenceSegmentationResponse,
)
from app.services.process.process_query_service import list_processing_items
from app.services.process.sentence_processing_service import (
    get_latest_sentence_segmentation_result,
    get_sentence_cursor_page,
    segment_document_sentences,
)

router = APIRouter()
LOGGER = get_logger(__name__)
MODULE_FILE = __file__


def _validate_sentence_pagination(after_start_offset: int | None, limit: int) -> None:
    if after_start_offset is not None and after_start_offset < 0:
        raise ValueError("afterStartOffset must be greater than or equal to 0.")
    if limit < 1 or limit > 200:
        raise ValueError("limit must be between 1 and 200.")


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


@router.post(
    "/process/sentence_segmentation/{doc_id}",
    response_model=SentenceSegmentationResponse,
)
def segment_document_sentences_route(doc_id: str) -> SentenceSegmentationResponse:
    function_name = "segment_document_sentences_route"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        doc_id=doc_id,
    )

    try:
        response = segment_document_sentences(doc_id)
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            doc_id=doc_id,
            processing_id=response["processing"]["id"],
            sentence_count=response["sentenceCount"],
        )
        return response
    except FileNotFoundError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            doc_id=doc_id,
            error=str(error),
        )
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            doc_id=doc_id,
            error=str(error),
        )
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            doc_id=doc_id,
            error=str(error),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.get(
    "/documents/{doc_id}/sentence-segmentations/latest",
    response_model=SentenceSegmentationLatestResponse,
)
def get_latest_sentence_segmentation_route(doc_id: str) -> SentenceSegmentationLatestResponse:
    function_name = "get_latest_sentence_segmentation_route"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        doc_id=doc_id,
    )

    try:
        response = get_latest_sentence_segmentation_result(doc_id)
        latest_processing_id = None
        if response["processing"] is not None:
            latest_processing_id = response["processing"]["id"]
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            doc_id=doc_id,
            processing_id=latest_processing_id,
            sentence_count=response["sentenceCount"],
        )
        return response
    except FileNotFoundError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            doc_id=doc_id,
            error=str(error),
        )
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            doc_id=doc_id,
            error=str(error),
        )
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            doc_id=doc_id,
            error=str(error),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.get("/documents/{doc_id}/sentences", response_model=SentenceCursorPage)
def get_document_sentences_route(
    doc_id: str,
    processing_id: str = Query(..., alias="processingId"),
    after_start_offset: int | None = Query(default=None, alias="afterStartOffset"),
    limit: int = Query(default=20),
) -> SentenceCursorPage:
    function_name = "get_document_sentences_route"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        doc_id=doc_id,
        processing_id=processing_id,
        after_start_offset=after_start_offset,
        limit=limit,
    )

    try:
        _validate_sentence_pagination(after_start_offset=after_start_offset, limit=limit)
        response = get_sentence_cursor_page(
            doc_id=doc_id,
            processing_id=processing_id,
            after_start_offset=after_start_offset,
            limit=limit,
        )
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            doc_id=doc_id,
            processing_id=processing_id,
            result=len(response["items"]),
            has_more=response["hasMore"],
        )
        return response
    except FileNotFoundError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            doc_id=doc_id,
            processing_id=processing_id,
            error=str(error),
        )
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            doc_id=doc_id,
            processing_id=processing_id,
            error=str(error),
        )
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            doc_id=doc_id,
            processing_id=processing_id,
            error=str(error),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error") from error
