import json
import re
from collections.abc import Iterable, Iterator
from typing import TypeVar
# core
from app.core.process.multiprocessing import accelerate_lemma_io
# db
from app.infrastructure.repositories.lemma_repository import (map_lemma_row_to_dto, write_lemma_items_in_batch)
from app.infrastructure.repositories.processing_repository import (create_processing, get_processing_by_id,
    map_processing_row_to_dto,  update_processing_state)
from app.infrastructure.repositories.sentence_repository import get_all_sentences_by_segmentation_id
# sockets
from app.socket.socket_events import LEMMA_CREATED, PROCESS_CREATED, PROCESS_UPDATED
from app.socket.socket_publisher import publish_best_effort

try:
    from simplemma import lemmatize as simplemma_lemmatize
except ImportError:
    simplemma_lemmatize = None


LEMMATIZE_PROCESSING_TYPE = "lemmatize"
SENTENCE_SEGMENTATION_PROCESSING_TYPE = "sentence_segmentation"
TOKEN_PATTERN = re.compile(r"\s+|[^\W\d_]+(?:['’-][^\W\d_]+)*|\w+|[^\w\s]+", re.UNICODE)
T = TypeVar("T")


def _iter_batches(items: Iterable[T], batch_size: int) -> Iterator[list[T]]:
    batch: list[T] = []
    for item in items:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
            
    if batch:
        yield batch


def _lemma_sentence(source_text: str) -> str:
    if simplemma_lemmatize is None:
        raise RuntimeError("simplemma is required for sentence lemmatization.")

    if not source_text:
        return ""

    parts: list[str] = []
    for match in TOKEN_PATTERN.finditer(source_text):
        token = match.group(0)
        if token.isspace() or not any(character.isalpha() for character in token):
            parts.append(token)
            continue

        parts.append(simplemma_lemmatize(token, lang="de"))

    return "".join(parts)


def _build_lemma_row(sentence_row: dict[str, int | str | None], lemma_text: str) -> dict[str, str | None]:
    sentence_id = str(sentence_row["id"])
    start_offset = int(sentence_row["start_offset"])
    lemma_id = f"{sentence_id}_{start_offset}"
    source_text = str(sentence_row["source_text"] or "")
    return {
        "id": lemma_id,
        "doc_id": str(sentence_row["doc_id"]),
        "segmentation_id": str(sentence_row["processing_id"]),
        "sentence_id": sentence_id,
        "source_text": source_text,
        "lemma_text": lemma_text,
        "corrected_lemma": lemma_text,
        "fvg_result_id": None,
    }


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
    process_item = map_processing_row_to_dto(processing)
    publish_best_effort(PROCESS_CREATED, process_item)

    try:
        lemma_rows: list[dict[str, str | None]] = []
        preview_items: list[dict[str, object]] = []
        for sentence_batch in _iter_batches(get_all_sentences_by_segmentation_id(segmentation_id), batch_size=256):
            source_texts = [str(sentence_row["source_text"] or "") for sentence_row in sentence_batch]
            lemma_texts = accelerate_lemma_io(_lemma_sentence, source_texts)
            built_rows = [_build_lemma_row(sentence_row=sentence_row, lemma_text=lemma_text)
                for sentence_row, lemma_text in zip(sentence_batch, lemma_texts, strict=True)]
            lemma_rows.extend(built_rows)

            remaining_preview = preview_length - len(preview_items)
            if remaining_preview > 0:
                preview_items.extend(
                    map_lemma_row_to_dto(row)
                    for row in built_rows[:remaining_preview]
                )

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
