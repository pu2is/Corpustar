import json

from app.core.process.lemmatize import lemmatize_sentence_to_tokens
from app.core.process.worker.accelerate_io import accelerate_io
from app.infrastructure.repositories.lemma_tokens import (
    rm_lemma_tokens_by_version_id,
    save_lemma_token_in_batch,
)
from app.infrastructure.repositories.processings import (
    change_process_item_state,
    map_process_row_to_item,
    read_process_item_by_id,
    write_process_item,
)
from app.infrastructure.repositories.sentences import get_all_sentences_by_version_id
from app.socket.socket_events import LEMMATIZE_FAILED, LEMMATIZE_STARTED, LEMMATIZE_SUCCEED
from app.socket.socket_publisher import publish_best_effort


def lemmatize_sentences(segmentation_id: str) -> dict[str, object]:
    segmentation_process = read_process_item_by_id(segmentation_id)
    if segmentation_process is None:
        raise FileNotFoundError(f"Segmentation process not found: {segmentation_id}")
    if segmentation_process["type"] != "sentence_segmentation":
        raise ValueError(f"Process item is not sentence_segmentation: {segmentation_id}")

    doc_id = segmentation_process["doc_id"]
    process = write_process_item(
        doc_id=doc_id,
        parent_id=segmentation_id,
        type="lemma",
        state="running",
        meta_json=json.dumps({"segmentation_id": segmentation_id}),
    )
    lemma_process_id = str(process["id"])
    publish_best_effort(LEMMATIZE_STARTED, map_process_row_to_item(process))

    try:
        sentence_rows = list(get_all_sentences_by_version_id(segmentation_id))
        if not sentence_rows:
            raise ValueError(f"No sentences found for segmentation_id={segmentation_id}")

        def _worker(sentence_row: object) -> object:
            return lemmatize_sentence_to_tokens(sentence_row, version_id=lemma_process_id)

        token_groups = accelerate_io(_worker, sentence_rows)
        token_rows: list[dict[str, object]] = []
        for group in token_groups:
            token_rows.extend(group)  # type: ignore[arg-type]

        save_lemma_token_in_batch(token_rows, clear_existing=True)

        succeeded = change_process_item_state(lemma_process_id, "succeed")
        process_item = map_process_row_to_item(succeeded)
        publish_best_effort(LEMMATIZE_SUCCEED, process_item)
        return process_item

    except Exception as error:
        rm_lemma_tokens_by_version_id(lemma_process_id)
        failed = change_process_item_state(
            lemma_process_id,
            "failed",
            error_message=str(error),
        )
        process_item = map_process_row_to_item(failed)
        publish_best_effort(LEMMATIZE_FAILED, process_item)
        raise
