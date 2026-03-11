from datetime import datetime, timezone
from pathlib import Path

from app.core.doc_to_text import convert_document_to_text
from app.core.document_utils import calculate_sha256, get_file_size, get_file_type
from app.core.text_storage import save_text_content
from app.services.document_repository import insert_document


def add_document(file_path: str) -> dict:
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
    text_path = save_text_content(doc_id, text)
    now_iso = datetime.now(timezone.utc).isoformat()

    doc = {
        "id": doc_id,
        "filename": filename,
        "displayName": display_name,
        "note": note,
        "sourcePath": resolved_source_path,
        "textPath": text_path,
        "fileType": file_type,
        "fileSize": file_size,
        "createdAt": now_iso,
        "updatedAt": now_iso,
    }
    insert_document(doc)

    return doc
