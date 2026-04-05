from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from app.core.process.lemmatize import lemmatize_sentence_to_tokens
from app.core.process.predict_fvg_candidates import predict_fvg_candidates
from app.core.process.worker.accelerate_io import accelerate_io
from app.infrastructure.db.connection import connection_scope
from app.infrastructure.repositories.fvg_candidates import write_fvg_candidate_items
from app.infrastructure.repositories.fvg_entries import get_fvg_entries_by_rule_id
from app.infrastructure.repositories.lemma_tokens import (
    count_lemma_tokens_by_version_id,
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
from app.socket.socket_events import (
    FVG_MATCH_FINISHED,
    FVG_MATCH_LEMMATIZE_FINISHED,
    FVG_MATCH_LEMMATIZE_START,
    FVG_MATCH_START,
)
from app.socket.socket_publisher import publish_best_effort


def lemmatize_sentences_for_fvg_candidates(
    *,
    segmentation_id: str,
    lemma_version_id: str,
) -> list[dict[str, int | str]]:
    sentence_rows = list(get_all_sentences_by_version_id(segmentation_id))
    if not sentence_rows:
        raise ValueError(f"No sentences found for segmentation_id={segmentation_id}")

    def _worker(sentence_row: Mapping[str, int | str]) -> object:
        return lemmatize_sentence_to_tokens(sentence_row, version_id=lemma_version_id)

    token_groups = accelerate_io(_worker, sentence_rows)
    token_rows: list[dict[str, int | str]] = []
    for token_group in token_groups:
        token_rows.extend(token_group)  # type: ignore[arg-type]
    return token_rows


def run_fvg_candidate_matching(*, segmentation_id: str, rule_id: str) -> dict[str, object]:
    segmentation_process = read_process_item_by_id(segmentation_id)
    if segmentation_process is None:
        raise FileNotFoundError(f"Segmentation process not found: {segmentation_id}")
    if segmentation_process["type"] != "sentence_segmentation":
        raise ValueError(f"Process item is not sentence_segmentation: {segmentation_id}")

    doc_id = segmentation_process["doc_id"]
    request_meta: dict[str, Any] = {
        "segmentation_id": segmentation_id,
        "rule_id": rule_id,
    }

    fvg_process = write_process_item(
        doc_id=doc_id,
        parent_id=segmentation_id,
        type="fvg",
        state="running",
        meta=request_meta,
    )
    fvg_process_id = str(fvg_process["id"])
    publish_best_effort(FVG_MATCH_START, map_process_row_to_item(fvg_process))

    lemma_process = write_process_item(
        doc_id=doc_id,
        parent_id=fvg_process_id,
        type="lemma",
        state="running",
        meta={
            **request_meta,
            "src": "processing/fvgMatch",
        },
    )
    lemma_process_id = str(lemma_process["id"])
    publish_best_effort(FVG_MATCH_LEMMATIZE_START, map_process_row_to_item(lemma_process))

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            lemma_future = executor.submit(
                lemmatize_sentences_for_fvg_candidates,
                segmentation_id=segmentation_id,
                lemma_version_id=lemma_process_id,
            )
            entries_future = executor.submit(get_fvg_entries_by_rule_id, rule_id)

            lemma_token_rows = lemma_future.result()
            fvg_entries = entries_future.result()

        with connection_scope() as connection:
            save_lemma_token_in_batch(
                lemma_token_rows,
                clear_existing=True,
                connection=connection,
            )
            persisted_count = count_lemma_tokens_by_version_id(
                lemma_process_id,
                connection=connection,
            )
            if persisted_count != len(lemma_token_rows):
                raise RuntimeError(
                    "Lemma tokens persistence mismatch: "
                    f"expected={len(lemma_token_rows)} persisted={persisted_count}"
                )

            lemma_succeeded = change_process_item_state(
                lemma_process_id,
                "succeed",
                connection=connection,
            )
            connection.commit()

        publish_best_effort(
            FVG_MATCH_LEMMATIZE_FINISHED,
            map_process_row_to_item(lemma_succeeded),
        )

        candidates = predict_fvg_candidates(fvg_entries, lemma_token_rows)
        sentence_ids = list(
            dict.fromkeys(str(token_row["sentence_id"]) for token_row in lemma_token_rows)
        )
        write_fvg_candidate_items(
            candidates,
            clear_sentence_ids=sentence_ids,
        )

        fvg_succeeded = change_process_item_state(fvg_process_id, "succeed")
        fvg_process_item = map_process_row_to_item(fvg_succeeded)
        publish_best_effort(FVG_MATCH_FINISHED, fvg_process_item)
        return fvg_process_item
    except Exception as error:
        rm_lemma_tokens_by_version_id(lemma_process_id)
        lemma_failed = change_process_item_state(
            lemma_process_id,
            "failed",
            error_message=str(error),
        )
        publish_best_effort(
            FVG_MATCH_LEMMATIZE_FINISHED,
            map_process_row_to_item(lemma_failed),
        )

        fvg_failed = change_process_item_state(
            fvg_process_id,
            "failed",
            error_message=str(error),
        )
        fvg_process_item = map_process_row_to_item(fvg_failed)
        publish_best_effort(FVG_MATCH_FINISHED, fvg_process_item)
        raise
