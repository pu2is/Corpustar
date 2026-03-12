from typing import Any, TypeAlias, TypedDict

# Event names follow `domain:action`, for example:
# `document:updated`, `index:finished`, `chat:stream`.
SOCKET_CONNECTED = "socket:connected"
DOCUMENT_CREATED = "document:created"
DOCUMENT_REMOVED = "document:removed"

# `document:created` payload should be the full serialized document object.
DocumentCreatedPayload: TypeAlias = dict[str, Any]


class DocumentRemovedPayload(TypedDict):
    id: str
