import json
from pathlib import Path
from sqlite3 import Connection

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import get_connection
from app.core.log import get_logger, log_event
from app.schemas.documents import DocItem
from app.socket_manager import connection_manager
from app.services.add_document_service import add_document
from app.services.document_repository import get_all_documents
from app.services.remove_document_service import remove_document_with_text_cleanup

router = APIRouter()
LOGGER = get_logger(__name__)
MODULE_FILE = __file__


class AddDocumentRequest(BaseModel):
    filePath: str


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
def add_document_route(payload: AddDocumentRequest) -> dict:
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
            await connection_manager.broadcast(
                json.dumps(
                    {
                        "event": "document:removed",
                        "payload": {"id": id},
                    }
                )
            )
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
