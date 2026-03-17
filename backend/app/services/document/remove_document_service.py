from pathlib import Path

from app.core.log import get_logger, log_event
from app.infrastructure.repositories.document_repository import get_document_by_id, remove_document

LOGGER = get_logger(__name__)
MODULE_FILE = __file__


def remove_document_with_text_cleanup(document_id: str) -> dict:
    function_name = "remove_document_with_text_cleanup"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        id=document_id,
    )

    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        id=document_id,
        step="query_document",
    )
    document = get_document_by_id(document_id)
    if document is None:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            id=document_id,
            error="Document not found",
        )
        raise FileNotFoundError(f"Document not found: {document_id}")

    text_path = document.get("textPath")
    log_event(
        LOGGER,
        stage="OK",
        module_file=MODULE_FILE,
        function_name=function_name,
        id=document_id,
        step="document_found",
        text_path=text_path,
    )

    if text_path:
        text_file = Path(text_path)
        if text_file.exists() and text_file.is_file():
            try:
                text_file.unlink()
            except Exception as error:
                log_event(
                    LOGGER,
                    stage="ERROR",
                    module_file=MODULE_FILE,
                    function_name=function_name,
                    id=document_id,
                    text_path=text_path,
                    error=f"Failed to delete text file: {error}",
                    exc_info=True,
                )
                raise

            log_event(
                LOGGER,
                stage="OK",
                module_file=MODULE_FILE,
                function_name=function_name,
                id=document_id,
                step="text_file_deleted",
                text_path=text_path,
            )
        elif not text_file.exists():
            log_event(
                LOGGER,
                stage="OK",
                module_file=MODULE_FILE,
                function_name=function_name,
                id=document_id,
                step="text_file_missing_skip",
                text_path=text_path,
            )
        else:
            log_event(
                LOGGER,
                stage="ERROR",
                module_file=MODULE_FILE,
                function_name=function_name,
                id=document_id,
                text_path=text_path,
                error="textPath exists but is not a file",
            )
            raise RuntimeError(f"textPath is not a file: {text_path}")
    else:
        log_event(
            LOGGER,
            stage="OK",
            module_file=MODULE_FILE,
            function_name=function_name,
            id=document_id,
            step="text_path_empty_skip",
            text_path=text_path,
        )

    # Keep delete semantics at parent-row level and rely on DB-level
    # ON DELETE CASCADE to remove processings/document_sentences.
    is_removed = remove_document(document_id)
    if not is_removed:
        log_event(
            LOGGER,
            stage="ERROR",
            module_file=MODULE_FILE,
            function_name=function_name,
            id=document_id,
            text_path=text_path,
            error="Failed to remove document from database",
        )
        raise RuntimeError(f"Failed to remove document from database: {document_id}")

    log_event(
        LOGGER,
        stage="OK",
        module_file=MODULE_FILE,
        function_name=function_name,
        id=document_id,
        step="database_record_deleted",
        text_path=text_path,
    )

    return {
        "success": True,
        "id": document_id,
        "textPath": text_path,
    }
