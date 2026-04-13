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

FVG_MATCH_START = "fvgMatch:start"
FVG_MATCH_LEMMATIZE_START = "fvgMatch:lemmatizeStart"
FVG_MATCH_LEMMATIZE_FINISHED = "fvgMatch:lemmatizeFinished"
FVG_MATCH_FINISHED = "fvgMatch:finished"

IMPORT_RULE_STARTED = "importRule:started"
IMPORT_RULE_FAILED = "importRule:failed"
IMPORT_RULE_SUCCEED = "importRule:succeed"
IMPORT_FVG_ENTRIES_SUCCEED = "importFvgEntries:succeed"

SENTENCE_MERGED = "sentence:merged"
SENTENCE_CLIPPED = "sentence:clipped"
SENTENCE_CORRECTED = "sentence:corrected"

RULE_REMOVED = "rule:removed"
RULE_COPY_FINISHED = "ruleCopy:finished"

FVG_APPENDED = "fvg:appended"
FVG_REMOVED = "fvg:removed"
FVG_UPDATED = "fvg:updated"

FVG_CANDIDATE_REMOVE_FAILED = "fvgCandidate:removeFailed"
FVG_CANDIDATE_RESTORE_FAILED = "fvgCandidate:restoreFailed"
FVG_CANDIDATE_ADD_SUCCEED = "fvgCandidate:addSucceed"
FVG_CANDIDATE_ADD_FAILED = "fvgCandidate:addFailed"

FVG_RESULTS_REMOVED = "fvgResults:removed"

LEMMA_EDIT_SUCCEED = "lemmaEdit:succeed"
LEMMA_EDIT_FAILED = "lemmaEdit:failed"


SocketPayload: TypeAlias = dict[str, Any]


class SocketEnvelope(TypedDict):
    event: str
    payload: Any


def make_envelope(event: str, payload: Any = None) -> SocketEnvelope:
    return {
        "event": event,
        "payload": payload if payload is not None else {},
    }
