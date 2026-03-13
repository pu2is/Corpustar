from typing import Any, TypeAlias, TypedDict

# Event names follow `domain:action`, for example:
# `document:updated`, `index:finished`, `chat:stream`.
SOCKET_CONNECTED = "socket:connected"
DOCUMENT_CREATED = "document:created"
DOCUMENT_REMOVED = "document:removed"
PROCESSING_CREATED = "processing:created"
PROCESSING_UPDATED = "processing:updated"
SENTENCE_LIST_REBUILT = "sentence:list_rebuilt"
SENTENCE_MERGED = "sentence:merged"
SENTENCE_CLIPPED = "sentence:clipped"

# `document:created` payload should be the full serialized document object.
DocumentCreatedPayload: TypeAlias = dict[str, Any]


class DocumentRemovedPayload(TypedDict):
    id: str


class SocketEnvelope(TypedDict):
    event: str
    payload: dict[str, Any]


def make_envelope(event: str, payload: dict[str, Any] | None = None) -> SocketEnvelope:
    return {
        "event": event,
        "payload": payload or {},
    }
