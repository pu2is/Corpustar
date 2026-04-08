from app.core.sentence.build_lemma_items import build_lemma_token_item_from_row
from app.infrastructure.repositories.lemma_tokens import find_lemma_tokens_by_sentence_ids_and_word

_VERB_POS_TAGS = ["VERB", "AUX"]


def filter_sentences_by_verb_lemma(
    sentence_ids: list[str],
    lemma_word: str,
) -> tuple[set[str], dict[str, list[dict]]]:
    """Return (matching_sentence_id_set, highlight_tokens_by_sentence_id).

    Only sentences that contain at least one lemma token with the given
    lemma_word and pos_tag VERB or AUX are included in the result.
    """
    rows_by_sentence_id = find_lemma_tokens_by_sentence_ids_and_word(
        sentence_ids=sentence_ids,
        lemma_word=lemma_word,
        pos_tags=_VERB_POS_TAGS,
    )
    highlight_by_sentence_id: dict[str, list[dict]] = {
        sentence_id: [build_lemma_token_item_from_row(row) for row in rows]
        for sentence_id, rows in rows_by_sentence_id.items()
    }
    matched_ids = set(highlight_by_sentence_id.keys())
    return matched_ids, highlight_by_sentence_id
