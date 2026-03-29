// Canonical backend socket event dictionary.
// Keep this file in sync with backend/app/socket/socket_events.py.
export const SOCKET_EVENT = {
  SOCKET_CONNECTED: 'socket:connected',
  SOCKET_DISCONNECTED: 'socket:disconnected',

  DOCUMENT_CREATED: 'document:created',
  DOCUMENT_REMOVED: 'document:removed',

  SEGMENTATION_STARTED: 'segmentation:started',
  SEGMENTATION_FAILED: 'segmentation:failed',
  SEGMENTATION_SUCCEED: 'segmentation:succeed',

  LEMMATIZE_STARTED: 'lemmatize:started',
  LEMMATIZE_FAILED: 'lemmatize:failed',
  LEMMATIZE_SUCCEED: 'lemmatize:succeed',

  IMPORT_RULE_STARTED: 'importRule:started',
  IMPORT_RULE_FAILED: 'importRule:failed',
  IMPORT_RULE_SUCCEED: 'importRule:succeed',
  IMPORT_FVG_ENTRIES_SUCCEED: 'importFvgEntries:succeed',

  SENTENCE_MERGED: 'sentence:merged',
  SENTENCE_CLIPPED: 'sentence:clipped',
  SENTENCE_CORRECTED: 'sentence:corrected',

  RULE_ITEM_REMOVED: 'ruleItem:removed',

  FVG_APPENDED: 'fvg:appended',
  FVG_REMOVED: 'fvg:removed',
  FVG_UPDATED: 'fvg:updated',
} as const

export type BackendSocketEventName = (typeof SOCKET_EVENT)[keyof typeof SOCKET_EVENT]
