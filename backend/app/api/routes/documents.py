from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.log import get_logger, log_event
from app.schemas.documents import DocItem, DocumentActionResponse
from app.services.document.add_document_service import add_document
from app.services.document.document_query_service import list_documents
from app.services.document.remove_document_service import remove_document_with_text_cleanup
from app.socket.socket_events import DOCUMENT_CREATED, DOCUMENT_REMOVED
from app.socket.socket_publisher import publish

router = APIRouter()
LOGGER = get_logger(__name__)
MODULE_FILE = __file__


class AddDocumentRequest(BaseModel):
    file_path: str = Field(validation_alias="filePath")


@router.get("/documents")
def get_documents_route() -> list[DocItem]:
    function_name = "get_documents_route"
    log_event(LOGGER, stage="CALL", module_file=MODULE_FILE, function_name=function_name)

    try:
        documents = list_documents()
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


@router.post("/documents", response_model=DocumentActionResponse)
async def add_document_route(payload: AddDocumentRequest) -> DocumentActionResponse | JSONResponse:
    function_name = "add_document_route"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        file_path=payload.file_path,
    )

    try:
        doc = add_document(payload.file_path)

        try:
            await publish(DOCUMENT_CREATED, doc)
        except Exception as broadcast_error:
            log_event(
                LOGGER,
                stage="ERROR",
                module_file=MODULE_FILE,
                function_name=function_name,
                file_path=payload.file_path,
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
        return {"id": str(doc["id"]), "ok": True, "err_msg": ""}

    except FileNotFoundError as error:
        return JSONResponse(
            status_code=404,
            content={"id": "", "ok": False, "err_msg": "File not found"},
        )
    except ValueError as error:
        return JSONResponse(
            status_code=400,
            content={"id": "", "ok": False, "err_msg": str(error)},
        )
    except RuntimeError as error:
        if Path(payload.file_path).suffix.lower() == ".doc":
            return JSONResponse(
                status_code=400,
                content={"id": "", "ok": False, "err_msg": str(error)},
            )
        return JSONResponse(
            status_code=500,
            content={"id": "", "ok": False, "err_msg": "Internal server error"},
        )
    except Exception as error:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            file_path=payload.file_path,
            error=str(error),
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"id": "", "ok": False, "err_msg": "Internal server error"},
        )


@router.delete("/documents/{id}", response_model=DocumentActionResponse)
async def remove_document_route(id: str) -> DocumentActionResponse | JSONResponse:
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

        return {"id": id, "ok": True, "err_msg": ""}
    except FileNotFoundError as error:
        return JSONResponse(
            status_code=404,
            content={"id": id, "ok": False, "err_msg": "Document not found"},
        )
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
        return JSONResponse(
            status_code=500,
            content={"id": id, "ok": False, "err_msg": "Internal server error"},
        )
