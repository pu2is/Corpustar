import json
# core
from app.core.process.multiprocessing import accelerate_lemma_io
from app.core.process.simplemma import (build_lemma_rows, iter_sentence_batches, lemmatize_german_text)
from app.core.sentence.build_lemma_items import build_lemma_item_from_row
# db
from app.infrastructure.repositories.lemma_repository import write_lemma_items_in_batch
from app.infrastructure.repositories.processing_repository import (create_processing, get_processing_by_id,
    map_processing_row_to_dto, update_processing_state)
from app.infrastructure.repositories.sentence_repository import get_all_sentences_by_segmentation_id
# socket
from app.socket.socket_events import LEMMA_CREATED, PROCESS_CREATED, PROCESS_UPDATED
from app.socket.socket_publisher import publish_best_effort


LEMMATIZE_PROCESSING_TYPE = "lemmatize"
SENTENCE_SEGMENTATION_PROCESSING_TYPE = "sentence_segmentation"


def lemma_batch_io(segmentation_id: str, preview_length: int = 0) -> None:
    segmentation_processing = get_processing_by_id(segmentation_id)
    if segmentation_processing is None:
        raise FileNotFoundError(f"Segmentation process not found: {segmentation_id}")
    if segmentation_processing["type"] != SENTENCE_SEGMENTATION_PROCESSING_TYPE:
        raise ValueError(f"Processing is not a sentence segmentation: {segmentation_id}")

    doc_id = str(segmentation_processing["doc_id"])
    processing = create_processing(
        doc_id=doc_id,
        type=LEMMATIZE_PROCESSING_TYPE,
        state="running",
        meta_json=json.dumps({"segmentationId": segmentation_id}),
    )
    processing_id = str(processing["id"])
    publish_best_effort(PROCESS_CREATED, map_processing_row_to_dto(processing))

    try:
        lemma_rows: list[dict[str, str | None]] = []
        preview_items: list[dict[str, object]] = []
        for sentence_batch in iter_sentence_batches(
            get_all_sentences_by_segmentation_id(segmentation_id),
        ):
            source_texts = [str(sentence_row["source_text"] or "") for sentence_row in sentence_batch]
            lemma_texts = accelerate_lemma_io(lemmatize_german_text, source_texts)
            built_rows = build_lemma_rows(sentence_batch, lemma_texts)
            lemma_rows.extend(built_rows)

            remaining_preview = preview_length - len(preview_items)
            if remaining_preview > 0:
                preview_items.extend(build_lemma_item_from_row(row) for row in built_rows[:remaining_preview])

        if not lemma_rows:
            raise ValueError(f"No sentence items found for segmentation_id={segmentation_id}")

        write_lemma_items_in_batch(lemma_rows, clear_existing=True)
        if preview_items:
            publish_best_effort(LEMMA_CREATED, preview_items)

        succeeded_processing = update_processing_state(
            processing_id=processing_id,
            new_state="succeed",
        )
        publish_best_effort(PROCESS_UPDATED, map_processing_row_to_dto(succeeded_processing))
    except Exception as error:
        failed_processing = update_processing_state(
            processing_id=processing_id,
            new_state="failed",
            error_message=str(error),
        )
        publish_best_effort(PROCESS_UPDATED, map_processing_row_to_dto(failed_processing))
        raise
