import importlib
import sys

_LEGACY_MODULE_ALIASES = {
    "add_document_service": "app.services.document.add_document_service",
    "document_repository": "app.infrastructure.repositories.document_repository",
    "remove_document_service": "app.services.document.remove_document_service",
    "processing_repository": "app.infrastructure.repositories.processing_repository",
    "sentence_edit_service": "app.services.sentence.sentence_edit_service",
    "sentence_processing_service": "app.services.process.sentence_segmentation",
    "sentence_repository": "app.infrastructure.repositories.sentence_repository",
    "sentence_segmentation_service": "app.services.process.sentence_segmentation",
}


for legacy_name, target_module in _LEGACY_MODULE_ALIASES.items():
    sys.modules[f"{__name__}.{legacy_name}"] = importlib.import_module(target_module)
