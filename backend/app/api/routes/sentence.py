from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.core.log import get_logger, log_event
from app.schemas.sentences import (
    MergeSentenceRequest,
    SentenceActionResponse,
    SentenceClipRequest,
    SentenceCorrectRequest,
    SentenceCursorPageRequest,
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


@router.post("/sentences", response_model=list[SentenceItem])
def get_document_sentences(payload: SentenceCursorPageRequest) -> list[SentenceItem]:
    function_name = "get_document_sentences"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        doc_id=payload.doc_id,
        segmentation_id=payload.segmentation_id,
        split_offset=payload.split_offset,
        limit=payload.limit,
    )

    try:
        page = get_sentence_cursor_page(
            doc_id=payload.doc_id,
            segmentation_id=payload.segmentation_id,
            split_offset=payload.split_offset,
            limit=payload.limit,
        )
        return page["items"]
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
            doc_id=payload.doc_id,
            segmentation_id=payload.segmentation_id,
            error=str(error),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post("/sentence/merge", response_model=SentenceActionResponse)
def merge_sentences_route(payload: MergeSentenceRequest) -> SentenceActionResponse | JSONResponse:
    try:
        merged_item = merge_sentences(
            payload.sentence_ids,
            socket_meta=payload.model_dump(),
        )
        return {"id": merged_item["id"], "ok": True, "error_msg": ""}
    except FileNotFoundError as error:
        return JSONResponse(
            status_code=404,
            content={"id": "", "ok": False, "error_msg": str(error)},
        )
    except ValueError as error:
        return JSONResponse(
            status_code=400,
            content={"id": "", "ok": False, "error_msg": str(error)},
        )
    except Exception as error:
        return JSONResponse(
            status_code=500,
            content={"id": "", "ok": False, "error_msg": "Internal server error"},
        )


@router.post("/sentence/clip", response_model=SentenceActionResponse)
def clip_sentence_route(payload: SentenceClipRequest) -> SentenceActionResponse | JSONResponse:
    try:
        clip_sentence(
            sentence_id=payload.sentence_id,
            split_offset=payload.split_offset,
            socket_meta=payload.model_dump(),
        )
        return {"id": payload.sentence_id, "ok": True, "error_msg": ""}
    except FileNotFoundError as error:
        return JSONResponse(
            status_code=404,
            content={"id": payload.sentence_id, "ok": False, "error_msg": str(error)},
        )
    except ValueError as error:
        return JSONResponse(
            status_code=400,
            content={"id": payload.sentence_id, "ok": False, "error_msg": str(error)},
        )
    except Exception as error:
        return JSONResponse(
            status_code=500,
            content={"id": payload.sentence_id, "ok": False, "error_msg": "Internal server error"},
        )


@router.post("/sentence/correct", response_model=SentenceActionResponse)
def correct_sentence_route(payload: SentenceCorrectRequest) -> SentenceActionResponse | JSONResponse:
    try:
        sentence = correct_sentence(
            sentence_id=payload.sentence_id,
            corrected_text=payload.corrected_text,
        )
        return {"id": sentence["id"], "ok": True, "error_msg": ""}
    except FileNotFoundError as error:
        return JSONResponse(
            status_code=404,
            content={"id": payload.sentence_id, "ok": False, "error_msg": str(error)},
        )
    except ValueError as error:
        return JSONResponse(
            status_code=400,
            content={"id": payload.sentence_id, "ok": False, "error_msg": str(error)},
        )
    except Exception as error:
        return JSONResponse(
            status_code=500,
            content={"id": payload.sentence_id, "ok": False, "error_msg": "Internal server error"},
        )
