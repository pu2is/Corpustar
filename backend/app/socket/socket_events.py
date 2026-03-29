from typing import Any, TypeAlias, TypedDict


SOCKET_CONNECTED = "socket:connected"

DOCUMENT_CREATED = "document:created"
DOCUMENT_REMOVED = "document:removed"

SEGMENTATION_STARTED = "segmentation:started"
SEGMENTATION_FAILED = "segmentation:failed"
SEGMENTATION_SUCCEED = "segmentation:succeed"

LEMMATIZE_STARTED = "lemmatize:started"
LEMMATIZE_FAILED = "lemmatize:failed"
LEMMATIZE_SUCCEED = "lemmatize:succeed"

IMPORT_RULE_STARTED = "importRule:started"
IMPORT_RULE_FAILED = "importRule:failed"
IMPORT_RULE_SUCCEED = "importRule:succeed"
IMPORT_FVG_ENTRIES_SUCCEED = "importFvgEntries:succeed"

SENTENCE_MERGED = "sentence:merged"
SENTENCE_CLIPPED = "sentence:clipped"
SENTENCE_CORRECTED = "sentence:corrected"

RULE_ITEM_REMOVED = "ruleItem:removed"

FVG_APPENDED = "fvg:appended"
FVG_REMOVED = "fvg:removed"
FVG_UPDATED = "fvg:updated"

# Legacy aliases kept for compatibility.
PROCESS_CREATED = SEGMENTATION_STARTED
PROCESS_UPDATED = SEGMENTATION_SUCCEED
PROCESSING_CREATED = PROCESS_CREATED
PROCESSING_UPDATED = PROCESS_UPDATED
RULE_CREATED = IMPORT_RULE_SUCCEED
RULE_REMOVED = RULE_ITEM_REMOVED
FVG_RULES_CREATED = IMPORT_FVG_ENTRIES_SUCCEED
FVG_RULES_REMOVED = RULE_ITEM_REMOVED
FVG_RULE_APPENDED = FVG_APPENDED
FVG_RULE_REMOVED = FVG_REMOVED
FVG_RULE_UPDATED = FVG_UPDATED
LEMMA_CREATED = LEMMATIZE_SUCCEED
LEMMA_UPDATED = SENTENCE_CORRECTED


SocketPayload: TypeAlias = dict[str, Any]


class SocketEnvelope(TypedDict):
    event: str
    payload: Any


def make_envelope(event: str, payload: Any = None) -> SocketEnvelope:
    return {
        "event": event,
        "payload": payload if payload is not None else {},
    }
