from app.core.sentence.build_lemma_items import build_lemma_item_from_row
from app.infrastructure.repositories.lemma_repository import get_n_lemma_from


def get_lemma_items(segmentation_id: str, start_lemma_id: str | None, limit: int) -> list[dict[str, object]]:
    return [build_lemma_item_from_row(row)
        for row in get_n_lemma_from(
            segmentation_id=segmentation_id,
            start_from_id=start_lemma_id,
            limit=limit,
        )]
