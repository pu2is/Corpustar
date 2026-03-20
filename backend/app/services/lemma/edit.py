from app.infrastructure.repositories.lemma_repository import (
    map_lemma_row_to_dto,
    modify_lemma_item,
)
from app.socket.socket_events import LEMMA_UPDATED
from app.socket.socket_publisher import publish_best_effort


def correct_lemma(lemma_id: str, corrected_lemma: str) -> dict[str, object]:
    normalized_lemma = corrected_lemma.strip()
    if not normalized_lemma:
        raise ValueError("corrected_lemma is required")

    lemma_row = modify_lemma_item(lemma_id=lemma_id, new_lemma=normalized_lemma)
    lemma_item = map_lemma_row_to_dto(lemma_row)
    publish_best_effort(LEMMA_UPDATED, lemma_item)
    return lemma_item
