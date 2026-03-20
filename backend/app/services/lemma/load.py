from app.infrastructure.repositories.lemma_repository import (
    get_n_lemma_from,
    map_lemma_row_to_dto,
)


def get_lemma_items(segmentation_id: str, start_lemma_id: str | None, limit: int) -> list[dict[str, object]]:
    return [map_lemma_row_to_dto(row)
        for row in get_n_lemma_from(
            segmentation_id=segmentation_id,
            start_from_id=start_lemma_id,
            limit=limit,
        )]
