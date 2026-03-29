from app.infrastructure.repositories.processings import get_all_processes, map_process_row_to_item
from app.services.process.types import ProcessingItemDict


def list_processing_items() -> list[ProcessingItemDict]:
    return [map_process_row_to_item(row) for row in get_all_processes()]
