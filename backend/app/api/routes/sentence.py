from fastapi import APIRouter, HTTPException, Query

from app.core.log import get_logger, log_event
from app.schemas.sentences import (
    MergeSentenceRequest,
    SentenceClipRequest,
    SentenceClipResponse,
    SentenceCorrectRequest,
    SentenceCursorPage,
    SentenceItem,
)
from app.services.sentence.pagination import get_sentence_cursor_page
from app.services.sentence.sentence_edit_service import (
    clip_sentence,
    correct_sentence,
    merge_sentences,
)

router = APIRouter()
LOGGER = get_logger(__name__)
MODULE_FILE = __file__


@router.get("/sentences/{doc_id}", response_model=SentenceCursorPage)
def get_document_sentences(
    doc_id: str,
    segmentation_id: str = Query(..., alias="segmentationId"),
    after_start_offset: int | None = Query(default=None, alias="afterStartOffset"),
    limit: int = Query(..., ge=1),
) -> SentenceCursorPage:
    function_name = "get_document_sentences"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        doc_id=doc_id,
        segmentation_id=segmentation_id,
        after_start_offset=after_start_offset,
        limit=limit,
    )

    try:
        response = get_sentence_cursor_page(
            doc_id=doc_id,
            segmentation_id=segmentation_id,
            after_start_offset=after_start_offset,
            limit=limit,
        )
        return response
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            doc_id=doc_id,
            segmentation_id=segmentation_id,
            error=str(error),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/sentences/merge", response_model=SentenceItem)
def merge_sentences_route(payload: MergeSentenceRequest) -> SentenceItem:
    try:
        return merge_sentences(payload.sentence_ids)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/sentence/clip", response_model=SentenceClipResponse)
def clip_sentence_route(payload: SentenceClipRequest) -> SentenceClipResponse:
    try:
        return clip_sentence(
            sentence_id=payload.sentence_id,
            split_offset=payload.split_offset,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/sentence/correct", response_model=SentenceItem)
def correct_sentence_route(payload: SentenceCorrectRequest) -> SentenceItem:
    try:
        return correct_sentence(
            sentence_id=payload.sentence_id,
            corrected_text=payload.corrected_text,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Internal server error") from error
