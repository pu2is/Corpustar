from app.infrastructure.repositories.fvg_candidates import rm_fvg_candidates_by_process_id
from app.infrastructure.repositories.lemma_tokens import rm_lemma_tokens_by_version_id
from app.infrastructure.repositories.processings import (
    read_process_item_by_id,
    read_process_items_by_parent_id,
    rm_process_item,
)
from app.socket.socket_events import FVG_RESULTS_REMOVED
from app.socket.socket_publisher import publish_best_effort


def remove_results_by_fvg_process_id(fvg_process_id: str) -> None:
    fvg_process = read_process_item_by_id(fvg_process_id)
    if fvg_process is None:
        raise FileNotFoundError(f"FVG process not found: {fvg_process_id}")
    if fvg_process["type"] != "fvg":
        raise ValueError(f"Process is not of type 'fvg': {fvg_process_id}")

    child_processes = read_process_items_by_parent_id(fvg_process_id)
    lemma_process = next(
        (p for p in child_processes if p["type"] == "lemma"),
        None,
    )
    if lemma_process is None:
        raise FileNotFoundError(f"Lemma process not found for fvg_process_id: {fvg_process_id}")

    lemma_process_id = str(lemma_process["id"])

    rm_fvg_candidates_by_process_id(fvg_process_id)
    rm_lemma_tokens_by_version_id(lemma_process_id)
    rm_process_item(fvg_process_id)
    rm_process_item(lemma_process_id)

    publish_best_effort(
        FVG_RESULTS_REMOVED,
        {"fvg_process_id": fvg_process_id, "lemma_process_id": lemma_process_id},
    )
