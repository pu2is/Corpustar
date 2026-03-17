import importlib
import sys

_LEGACY_MODULE_ALIASES = {
    "doc_to_text": "app.core.document.doc_to_text",
    "document_utils": "app.core.document.document_utils",
    "text_storage": "app.core.document.text_storage",
}


for legacy_name, target_module in _LEGACY_MODULE_ALIASES.items():
    sys.modules[f"{__name__}.{legacy_name}"] = importlib.import_module(target_module)
