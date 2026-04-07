import uuid

from app.infrastructure.repositories.fvg_candidates import change_fvg_candidate_item, write_fvg_candidate_item
from app.infrastructure.repositories.lemma_tokens import get_lemma_tokens_by_ids
from app.infrastructure.repositories.sentences import get_sentence_by_id
from app.socket.socket_events import (
    FVG_CANDIDATE_ADD_FAILED,
    FVG_CANDIDATE_ADD_SUCCEED,
    FVG_CANDIDATE_REMOVE_FAILED,
    FVG_CANDIDATE_RESTORE_FAILED,
)
from app.socket.socket_publisher import publish_best_effort


def _get_doc_id_from_sentence(sentence_id: str) -> str:
    row = get_sentence_by_id(sentence_id)
    if row is None:
        return ""
    return str(row.get("doc_id", ""))


def remove_fvg_candidate(fvg_candidate_id: str, sentence_id: str) -> dict:
    try:
        updated = change_fvg_candidate_item(fvg_candidate_id, removed=True)
        return {"sentence_id": sentence_id, "fvg_candidate": updated}
    except Exception as err:
        doc_id = _get_doc_id_from_sentence(sentence_id)
        publish_best_effort(
            FVG_CANDIDATE_REMOVE_FAILED,
            {"sentence_id": sentence_id, "doc_id": doc_id, "err_msg": str(err)},
        )
        raise


def restore_fvg_candidate(fvg_candidate_id: str, sentence_id: str) -> dict:
    try:
        updated = change_fvg_candidate_item(fvg_candidate_id, removed=False)
        return {"sentence_id": sentence_id, "fvg_candidate": updated}
    except Exception as err:
        doc_id = _get_doc_id_from_sentence(sentence_id)
        publish_best_effort(
            FVG_CANDIDATE_RESTORE_FAILED,
            {"sentence_id": sentence_id, "doc_id": doc_id, "err_msg": str(err)},
        )
        raise


def add_fvg_candidate(sentence_id: str, process_id: str, fvg_entry_id: str,
    verb_id: str, noun_id: str, prep_id: str) -> dict:
    ids_to_fetch = [verb_id, noun_id] + ([prep_id] if prep_id else [])
    lemma_map = get_lemma_tokens_by_ids(ids_to_fetch)

    verb_lemma = lemma_map.get(verb_id)
    noun_lemma = lemma_map.get(noun_id)
    prep_lemma = lemma_map.get(prep_id) if prep_id else None

    if verb_lemma is None:
        raise FileNotFoundError(f"Lemma token not found: {verb_id}")
    if noun_lemma is None:
        raise FileNotFoundError(f"Lemma token not found: {noun_id}")

    row: dict = {
        "id": str(uuid.uuid4()),
        "sentence_id": sentence_id,
        "process_id": process_id,
        "algo_fvg_entry_id": fvg_entry_id,
        "corrected_fvg_entry_id": "",
        "algo_verb_token": str(verb_lemma["lemma_word"]),
        "algo_verb_index": int(verb_lemma["word_index"]),
        "corrected_verb_token": "",
        "corrected_verb_index": -1,
        "algo_noun_token": str(noun_lemma["lemma_word"]),
        "algo_noun_index": int(noun_lemma["word_index"]),
        "corrected_noun_token": "",
        "corrected_noun_index": -1,
        "algo_prep_token": str(prep_lemma["lemma_word"]) if prep_lemma else "",
        "algo_prep_index": int(prep_lemma["word_index"]) if prep_lemma else -1,
        "corrected_prep_token": "",
        "corrected_prep_index": -1,
        "label": "",
        "manuelle_created": True,
        "removed": False,
    }

    try:
        written = write_fvg_candidate_item(row)
        publish_best_effort(FVG_CANDIDATE_ADD_SUCCEED, {"ok": True, "err_msg": ""})
        return {"sentence_id": sentence_id, "fvg_candidate": written}
    except Exception as err:
        publish_best_effort(FVG_CANDIDATE_ADD_FAILED, {"ok": False, "err_msg": str(err)})
        raise
