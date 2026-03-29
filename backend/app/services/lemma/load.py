from app.core.sentence.build_lemma_items import build_lemma_token_item_from_row
from app.infrastructure.repositories.lemma_tokens import read_lemma_tokens_by_sentence_ids


def get_lemma_tokens_by_sentence_ids(
    *,
    sentence_ids: list[str],
) -> dict[str, list[dict[str, int | str]]]:
    normalized_sentence_ids = list(dict.fromkeys(_normalize_sentence_ids(sentence_ids)))
    if not normalized_sentence_ids:
        raise ValueError("sentence_ids is required")

    rows_by_sentence_id = read_lemma_tokens_by_sentence_ids(normalized_sentence_ids)
    return {
        sentence_id: [
            build_lemma_token_item_from_row(row)
            for row in rows_by_sentence_id.get(sentence_id, [])
        ]
        for sentence_id in normalized_sentence_ids
    }


def _normalize_sentence_ids(sentence_ids: list[str]) -> list[str]:
    return [sentence_id.strip() for sentence_id in sentence_ids if sentence_id and sentence_id.strip()]
