from app.core.document.document_utils import load_txt_by_path
from app.core.process.sentence_segmentation import segment_sentences
from app.core.sentence.build_sentence_items import build_sentence_item_from_row
from app.infrastructure.repositories.documents import read_document_by_id
from app.infrastructure.repositories.processings import (
    change_process_item_state,
    map_process_row_to_item,
    write_process_item,
)
from app.infrastructure.repositories.sentences import write_sentences_in_batch
from app.services.process.types import SentenceSegmentationResult
from app.socket.socket_events import SEGMENTATION_FAILED, SEGMENTATION_STARTED, SEGMENTATION_SUCCEED
from app.socket.socket_publisher import publish_best_effort


def segment_document_sentences(doc_id: str, preview_length: int) -> SentenceSegmentationResult:
    document = read_document_by_id(doc_id)
    if document is None:
        raise FileNotFoundError(f"Document not found: {doc_id}")

    full_text = load_txt_by_path(str(document["text_path"]))

    processing = write_process_item(
        doc_id=doc_id,
        type="sentence_segmentation",
        state="running",
        meta={
            "doc_id": doc_id,
            "preview_length": preview_length,
        },
    )
    process_item = map_process_row_to_item(processing)
    process_id = str(processing["id"])

    publish_best_effort(SEGMENTATION_STARTED, process_item)

    try:
        spans = segment_sentences(full_text)
        sentence_rows = write_sentences_in_batch(
            version_id=process_id,
            doc_id=doc_id,
            spans=spans,
            full_text=full_text,
        )

        processing = change_process_item_state(
            process_id=process_id,
            new_state="succeed",
        )
    except Exception as error:
        failed_process = change_process_item_state(
            process_id=process_id,
            new_state="failed",
            error_message=str(error),
        )
        publish_best_effort(SEGMENTATION_FAILED, map_process_row_to_item(failed_process))
        raise

    process_item = map_process_row_to_item(processing)
    sentence_items = [build_sentence_item_from_row(sentence_row=row, full_text=full_text) for row in sentence_rows]
    preview_items = sentence_items[:preview_length]
    publish_best_effort(
        SEGMENTATION_SUCCEED,
        {
            "processing": process_item,
            "preview": preview_items,
        },
    )

    return process_item
