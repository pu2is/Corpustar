from typing import Any, Literal, NotRequired, TypeAlias, TypedDict

# Event names follow `domain:action`, for example:
# `document:updated`, `index:finished`, `chat:stream`.
SOCKET_CONNECTED = "socket:connected"
DOCUMENT_CREATED = "document:created"
DOCUMENT_REMOVED = "document:removed"
PROCESSING_CREATED = "processing:created"
PROCESSING_UPDATED = "processing:updated"
SENTENCE_MERGED = "sentence:merged"
SENTENCE_CLIPPED = "sentence:clipped"
RULE_CREATED = "rule:created"
RULE_REMOVED = "rule:removed"
FVG_RULES_CREATED = "fvgRules:created"
FVG_RULES_REMOVED = "fvgRules:removed"
FVG_RULE_APPENDED = "fvgRule:appended"
FVG_RULE_REMOVED = "fvgRule:removed"
FVG_RULE_UPDATED = "fvgRule:updated"

# `document:created` payload should be the full serialized document object.
DocumentCreatedPayload: TypeAlias = dict[str, Any]


class DocumentRemovedPayload(TypedDict):
    id: str


class RuleCreatedPayload(TypedDict):
    id: str
    type: Literal["fvg"]
    path: str


class RuleRemovedPayload(TypedDict):
    id: str


class FvgRuleItemPayload(TypedDict):
    id: str
    ruleId: str
    verb: str
    phrase: str


class FvgRulesCreatedPayload(TypedDict):
    ruleId: str
    count: int
    items: NotRequired[list[FvgRuleItemPayload]]


class FvgRulesRemovedPayload(TypedDict):
    ruleId: str
    count: int


FvgRuleAppendedPayload: TypeAlias = FvgRuleItemPayload


class FvgRuleRemovedPayload(TypedDict):
    id: str
    ruleId: str


FvgRuleUpdatedPayload: TypeAlias = FvgRuleItemPayload


class SocketEnvelope(TypedDict):
    event: str
    payload: dict[str, Any]


def make_envelope(event: str, payload: dict[str, Any] | None = None) -> SocketEnvelope:
    return {
        "event": event,
        "payload": payload or {},
    }
