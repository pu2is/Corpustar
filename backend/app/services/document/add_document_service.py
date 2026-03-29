from datetime import datetime, timezone
from pathlib import Path

from app.core.document.doc_to_text import convert_document_to_text
from app.core.document.document_utils import calculate_sha256, get_file_size, get_file_type
from app.core.document.text_storage import save_text_content
from app.core.log import get_logger, log_event
from app.infrastructure.repositories.documents import write_document

LOGGER = get_logger(__name__)
MODULE_FILE = __file__


def add_document(file_path: str) -> dict[str, int | str]:
    function_name = "add_document"
    source_path = Path(file_path)
    if not source_path.exists():
        raise FileNotFoundError(file_path)

    resolved_source_path = str(source_path.resolve())
    file_type = get_file_type(resolved_source_path)
    doc_id = calculate_sha256(resolved_source_path)
    filename = source_path.name
    display_name = filename
    note = ""
    file_size = get_file_size(resolved_source_path)
    text = convert_document_to_text(resolved_source_path)
    char_count = len(text)
    text_path = save_text_content(doc_id, text)

    if file_type != "txt":
        legacy_txt_path = source_path.with_suffix(".txt")
        if legacy_txt_path.exists():
            try:
                if legacy_txt_path.resolve() != Path(text_path).resolve():
                    legacy_txt_path.unlink()
            except Exception as error:
                log_event(
                    LOGGER,
                    stage="ERROR",
                    module_file=MODULE_FILE,
                    function_name=function_name,
                    file_path=resolved_source_path,
                    text_path=text_path,
                    legacy_txt_path=str(legacy_txt_path),
                    error=f"Legacy sibling txt cleanup failed: {error}",
                    exc_info=True,
                )

    now_iso = datetime.now(timezone.utc).isoformat()

    document = {
        "id": doc_id,
        "filename": filename,
        "display_name": display_name,
        "note": note,
        "source_path": resolved_source_path,
        "text_path": text_path,
        "char_count": char_count,
        "file_type": file_type,
        "file_size": file_size,
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    write_document(document)

    return document
