from pathlib import Path

from app.core.log import get_logger, log_event
from app.infrastructure.db.connection import connection_scope
from app.infrastructure.repositories.documents import read_document_by_id, rm_document
from app.infrastructure.repositories.fvg_candidates import rm_fvg_candidate_items_by_sentence_ids
from app.infrastructure.repositories.lemma_tokens import rm_lemma_tokens_by_version_id
from app.infrastructure.repositories.processings import get_all_processes, rm_processes_by_doc_id
from app.infrastructure.repositories.sentences import get_sentence_ids_by_doc_id, rm_sentences_by_doc_id

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

    with connection_scope() as connection:
        # 1. Collect sentence IDs and segmentation version IDs before deleting anything
        sentence_ids = get_sentence_ids_by_doc_id(document_id, connection=connection)

        all_processes = get_all_processes()
        doc_processes = [p for p in all_processes if p.get("doc_id") == document_id]
        segmentation_version_ids = [
            p["id"] for p in doc_processes if p.get("type") == "sentence_segmentation"
        ]

        # 2. Delete fvg candidates linked to those sentences
        if sentence_ids:
            rm_fvg_candidate_items_by_sentence_ids(sentence_ids, connection=connection)

        # 3. Delete lemma tokens by segmentation version id
        for version_id in segmentation_version_ids:
            rm_lemma_tokens_by_version_id(version_id, connection=connection)

        # 4. Delete sentences
        rm_sentences_by_doc_id(document_id, connection=connection)

        # 5. Delete all process items for this document
        rm_processes_by_doc_id(document_id, connection=connection)

        # 6. Delete the document record itself
        deleted = rm_document(document_id, connection=connection)
        if not deleted:
            raise RuntimeError(f"Failed to remove document from database: {document_id}")

        connection.commit()

    # 7. Remove text file from disk (after DB is committed)
    if text_path:
        text_file = Path(text_path)
        if text_file.exists() and text_file.is_file():
            text_file.unlink()
        elif text_file.exists() and not text_file.is_file():
            raise RuntimeError(f"text_path is not a file: {text_path}")

    return {
        "success": True,
        "id": document_id,
        "text_path": text_path or None,
    }
