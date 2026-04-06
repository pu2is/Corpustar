from app.infrastructure.repositories.fvg_candidates import change_fvg_candidate_item
from app.infrastructure.repositories.sentences import get_sentence_by_id
from app.socket.socket_events import FVG_CANDIDATE_REMOVE_FAILED, FVG_CANDIDATE_RESTORE_FAILED
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
