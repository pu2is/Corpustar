from app.infrastructure.repositories.fvg_candidates import get_fvg_length_by_process_id
from app.infrastructure.repositories.lemma_tokens import (
    get_num_lemma_by_id_and_pos,
    get_num_unique_lemma_by_id_and_pos,
)
from app.infrastructure.repositories.processings import read_process_item_by_id, read_process_items_by_parent_id
from app.infrastructure.repositories.sentences import get_sentences_number_by_segmentation_id


def get_simple_statistics(fvg_process_id: str) -> dict[str, int]:
    fvg_process = read_process_item_by_id(fvg_process_id)
    if fvg_process is None:
        raise FileNotFoundError(f"FVG process not found: {fvg_process_id}")

    segmentation_id = str(fvg_process["parent_id"])

    lemma_process_items = read_process_items_by_parent_id(fvg_process_id)
    lemma_process = next(
        (p for p in lemma_process_items if str(p.get("type")) == "lemma"),
        None,
    )
    if lemma_process is None:
        raise FileNotFoundError(f"Lemma process not found for FVG process: {fvg_process_id}")

    lemmatize_id = str(lemma_process["id"])

    num_fvg = get_fvg_length_by_process_id(fvg_process_id)
    num_sentences = get_sentences_number_by_segmentation_id(segmentation_id)
    num_verb = get_num_lemma_by_id_and_pos(lemmatize_id, "VERB")
    num_aux = get_num_lemma_by_id_and_pos(lemmatize_id, "AUX")
    num_distinct_verbs = get_num_unique_lemma_by_id_and_pos(
        lemmatize_id,
        ["VERB", "AUX"],
    )

    return {
        "num_verb": num_verb,
        "num_aux": num_aux,
        "num_fvg": num_fvg,
        "num_sentences": num_sentences,
        "num_distinct_verbs": num_distinct_verbs,
    }
