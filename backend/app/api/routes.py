from sqlite3 import Connection
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import get_connection
from app.core.log import get_logger, log_event
from app.schemas.documents import DocItem
from app.services.add_document_service import add_document
from app.services.document_repository import get_all_documents

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
