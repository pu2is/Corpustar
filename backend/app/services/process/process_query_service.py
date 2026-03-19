from app.infrastructure.repositories.processing_repository import (
    list_processings,
    map_processing_row_to_dto,
)
from app.services.process.types import ProcessingItemDict


def list_processing_items() -> list[ProcessingItemDict]:
    return [map_processing_row_to_dto(row) for row in list_processings()]
