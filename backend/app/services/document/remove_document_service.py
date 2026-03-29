from pathlib import Path

from app.core.log import get_logger, log_event
from app.infrastructure.repositories.documents import read_document_by_id, rm_document

LOGGER = get_logger(__name__)
MODULE_FILE = __file__


def remove_document_with_text_cleanup(document_id: str) -> dict[str, str | bool | None]:
    function_name = "remove_document_with_text_cleanup"
    log_event(
        LOGGER,
        stage="CALL",
        module_file=MODULE_FILE,
        function_name=function_name,
        id=document_id,
    )

    document = read_document_by_id(document_id)
    if document is None:
        raise FileNotFoundError(f"Document not found: {document_id}")

    text_path = str(document.get("text_path", ""))

    if text_path:
        text_file = Path(text_path)
        if text_file.exists() and text_file.is_file():
            text_file.unlink()
        elif text_file.exists() and not text_file.is_file():
            raise RuntimeError(f"text_path is not a file: {text_path}")

    deleted = rm_document(document_id)
    if not deleted:
        raise RuntimeError(f"Failed to remove document from database: {document_id}")

    return {
        "success": True,
        "id": document_id,
        "text_path": text_path or None,
    }
