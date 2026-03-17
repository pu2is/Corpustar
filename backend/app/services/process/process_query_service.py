from app.infrastructure.repositories.processing_repository import (
    list_processings,
    map_processing_row_to_dto,
)


def list_processing_items() -> list[dict]:
    return [map_processing_row_to_dto(row) for row in list_processings()]
