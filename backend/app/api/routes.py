from pathlib import Path
from sqlite3 import Connection

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import get_connection
from app.core.log import get_logger, log_event
from app.schemas.documents import DocItem
from app.schemas.sentences import (
    ClipSentenceRequest,
    MergeSentenceRequest,
    SentenceCursorPage,
    SentenceItem,
    SentenceSegmentationLatestResponse,
    SentenceSegmentationResponse,
)
from app.socket.socket_events import DOCUMENT_CREATED, DOCUMENT_REMOVED
from app.socket.socket_publisher import publish
from app.services.add_document_service import add_document
from app.services.document_repository import get_all_documents
from app.services.remove_document_service import remove_document_with_text_cleanup
from app.services.sentence_edit_service import clip_sentence, merge_sentences
from app.services.sentence_processing_service import (
    get_latest_sentence_segmentation_result,
    get_sentence_cursor_page,
    segment_document_sentences,
)

router = APIRouter()
LOGGER = get_logger(__name__)
MODULE_FILE = __file__


class AddDocumentRequest(BaseModel):
    filePath: str


class ClipSentenceResponse(BaseModel):
    items: list[SentenceItem]


def _validate_sentence_pagination(after_start_offset: int | None, limit: int) -> None:
    if after_start_offset is not None and after_start_offset < 0:
        raise ValueError("afterStartOffset must be greater than or equal to 0.")
    if limit < 1 or limit > 200:
        raise ValueError("limit must be between 1 and 200.")


@router.get("/documents")
def get_documents_route() -> list[DocItem]:
    function_name = "get_documents_route"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
    )

    try:
        documents = get_all_documents()
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            result=len(documents),
        )
        return documents
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


@router.get("/health")
def health(connection: Connection = Depends(get_connection)):
    function_name = "health"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
    )

    try:
        connection.execute("SELECT 1").fetchone()
        response = {
            "status": "ok",
            "engine": "sqlite",
            "path": str(settings.sqlite_database_path),
        }
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            result=response["status"],
        )
        return response
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            error=str(error),
            exc_info=True,
        )
        raise


@router.post("/add_document")
async def add_document_route(payload: AddDocumentRequest) -> dict:
    function_name = "add_document_route"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        file_path=payload.filePath,
    )

    try:
        doc = add_document(payload.filePath)

        try:
            await publish(DOCUMENT_CREATED, doc)
        except Exception as broadcast_error:
            log_event(
                LOGGER,
                stage="ERROR",
                module_file=MODULE_FILE,
                function_name=function_name,
                file_path=payload.filePath,
                error=f"Broadcast failed: {broadcast_error}",
                exc_info=True,
            )

        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            result=doc["id"],
        )
        return doc
    except FileNotFoundError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            file_path=payload.filePath,
            error=str(error),
        )
        raise HTTPException(status_code=404, detail="File not found") from error
    except ValueError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            file_path=payload.filePath,
            error=str(error),
        )
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            file_path=payload.filePath,
            error=str(error),
        )
        if Path(payload.filePath).suffix.lower() == ".doc":
            raise HTTPException(status_code=400, detail=str(error)) from error
        raise HTTPException(status_code=500, detail="Internal server error") from error
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            file_path=payload.filePath,
            error=str(error),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.post(
    "/documents/{doc_id}/sentence-segmentations",
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


@router.post("/sentences/merge", response_model=SentenceItem)
def merge_sentences_route(payload: MergeSentenceRequest) -> SentenceItem:
    function_name = "merge_sentences_route"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        sentence_ids_count=len(payload.sentenceIds),
    )

    try:
        response = merge_sentences(payload.sentenceIds)
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            result=response["id"],
        )
        return response
    except FileNotFoundError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            error=str(error),
        )
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            error=str(error),
        )
        raise HTTPException(status_code=400, detail=str(error)) from error
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


@router.post("/sentences/{sentence_id}/clip", response_model=ClipSentenceResponse)
def clip_sentence_route(
    sentence_id: str,
    payload: ClipSentenceRequest,
) -> ClipSentenceResponse:
    function_name = "clip_sentence_route"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        sentence_id=sentence_id,
        split_offset=payload.splitOffset,
    )

    try:
        response = clip_sentence(
            sentence_id=sentence_id,
            split_offset=payload.splitOffset,
        )
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            sentence_id=sentence_id,
            result=len(response["items"]),
        )
        return response
    except FileNotFoundError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            sentence_id=sentence_id,
            error=str(error),
        )
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            sentence_id=sentence_id,
            error=str(error),
        )
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            sentence_id=sentence_id,
            error=str(error),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error") from error


@router.delete("/remove_document/{id}")
async def remove_document_route(id: str) -> dict:
    function_name = "remove_document_route"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        id=id,
    )

    try:
        remove_document_with_text_cleanup(id)

        try:
            await publish(DOCUMENT_REMOVED, {"id": id})
        except Exception as broadcast_error:
            log_event(
                LOGGER,
                stage="ERROR",
                module_file=MODULE_FILE,
                function_name=function_name,
                id=id,
                error=f"Broadcast failed: {broadcast_error}",
                exc_info=True,
            )

        response = {"success": True, "id": id}
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            result=id,
        )
        return response
    except FileNotFoundError as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            id=id,
            error=str(error),
        )
        raise HTTPException(status_code=404, detail="Document not found") from error
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            id=id,
            error=str(error),
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error") from error
