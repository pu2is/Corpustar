from app.core.lemma.edit import edit_lemma
from app.core.sentence.build_lemma_items import build_lemma_token_item_from_row
from app.infrastructure.repositories.lemma_tokens import (
    get_lemma_by_id,
    save_lemma_token_single,
)
from app.socket.socket_events import LEMMA_EDIT_FAILED, LEMMA_EDIT_SUCCEED
from app.socket.socket_publisher import publish_best_effort


def edit_lemma_token(lemma_id: str, new_lemma_word: str, new_pos_tag: str) -> dict:
    row = get_lemma_by_id(lemma_id)
    if row is None:
        raise ValueError(f"Lemma token '{lemma_id}' not found")

    # no-op: nothing changed
    if str(row["lemma_word"]) == new_lemma_word and str(row["pos_tag"]) == new_pos_tag:
        return build_lemma_token_item_from_row(row)

    try:
        updated_row = edit_lemma(row, new_lemma_word, new_pos_tag)
        save_lemma_token_single(updated_row)
        result = build_lemma_token_item_from_row(updated_row)
        publish_best_effort(LEMMA_EDIT_SUCCEED, result)
        return result
    except Exception:
        original = build_lemma_token_item_from_row(row)
        publish_best_effort(LEMMA_EDIT_FAILED, original)
        raise

