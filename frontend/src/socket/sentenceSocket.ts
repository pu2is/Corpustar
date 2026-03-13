import { on } from '@/socket/socket'

export const PROCESSING_CREATED = 'processing:created'
export const PROCESSING_UPDATED = 'processing:updated'
export const SENTENCE_LIST_REBUILT = 'sentence:list_rebuilt'
export const SENTENCE_MERGED = 'sentence:merged'
export const SENTENCE_CLIPPED = 'sentence:clipped'

export interface ProcessingEventPayload {
  docId: string
  processingId: string
  state?: string
  errorMessage?: string | null
}

export interface SentenceListRebuiltPayload {
  docId: string
  processingId: string
  sentenceCount: number
}

export interface SentenceMergedPayload {
  docId: string
  processingId: string
  mergedSentenceId: string
}

export interface SentenceClippedPayload {
  docId: string
  processingId: string
  sentenceId: string
}

export interface SentenceSocketHandlers {
  onProcessingCreated: (payload: ProcessingEventPayload) => void
  onProcessingUpdated: (payload: ProcessingEventPayload) => void
  onSentenceListRebuilt: (payload: SentenceListRebuiltPayload) => void
  onSentenceMerged: (payload: SentenceMergedPayload) => void
  onSentenceClipped: (payload: SentenceClippedPayload) => void
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function toNonEmptyString(value: unknown): string | null {
  if (typeof value !== 'string') {
    return null
  }

  const trimmed = value.trim()
  return trimmed.length ? trimmed : null
}

function toNonNegativeNumber(value: unknown): number | null {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) {
    return null
  }
  return value
}

function parseProcessingEventPayload(payload: unknown): ProcessingEventPayload | null {
  if (!isRecord(payload)) {
    return null
  }

  const docId = toNonEmptyString(payload.docId)
  const processingId = toNonEmptyString(payload.processingId)
  if (!docId || !processingId) {
    return null
  }

  const state = toNonEmptyString(payload.state) ?? undefined
  const errorMessage = payload.errorMessage === null
    ? null
    : (toNonEmptyString(payload.errorMessage) ?? undefined)

  return {
    docId,
    processingId,
    state,
    errorMessage,
  }
}

function parseSentenceListRebuiltPayload(payload: unknown): SentenceListRebuiltPayload | null {
  if (!isRecord(payload)) {
    return null
  }

  const docId = toNonEmptyString(payload.docId)
  const processingId = toNonEmptyString(payload.processingId)
  const sentenceCount = toNonNegativeNumber(payload.sentenceCount)
  if (!docId || !processingId || sentenceCount === null) {
    return null
  }

  return {
    docId,
    processingId,
    sentenceCount,
  }
}

function parseSentenceMergedPayload(payload: unknown): SentenceMergedPayload | null {
  if (!isRecord(payload)) {
    return null
  }

  const docId = toNonEmptyString(payload.docId)
  const processingId = toNonEmptyString(payload.processingId)
  const mergedSentenceId = toNonEmptyString(payload.mergedSentenceId)
  if (!docId || !processingId || !mergedSentenceId) {
    return null
  }

  return {
    docId,
    processingId,
    mergedSentenceId,
  }
}

function parseSentenceClippedPayload(payload: unknown): SentenceClippedPayload | null {
  if (!isRecord(payload)) {
    return null
  }

  const docId = toNonEmptyString(payload.docId)
  const processingId = toNonEmptyString(payload.processingId)
  const sentenceId = toNonEmptyString(payload.sentenceId)
  if (!docId || !processingId || !sentenceId) {
    return null
  }

  return {
    docId,
    processingId,
    sentenceId,
  }
}

export function bindSentenceSocketHandlers(
  handlers: SentenceSocketHandlers,
): Array<() => void> {
  const unbindProcessingCreated = on(PROCESSING_CREATED, (payload) => {
    const parsed = parseProcessingEventPayload(payload)
    if (parsed) {
      handlers.onProcessingCreated(parsed)
    }
  })

  const unbindProcessingUpdated = on(PROCESSING_UPDATED, (payload) => {
    const parsed = parseProcessingEventPayload(payload)
    if (parsed) {
      handlers.onProcessingUpdated(parsed)
    }
  })

  const unbindSentenceListRebuilt = on(SENTENCE_LIST_REBUILT, (payload) => {
    const parsed = parseSentenceListRebuiltPayload(payload)
    if (parsed) {
      handlers.onSentenceListRebuilt(parsed)
    }
  })

  const unbindSentenceMerged = on(SENTENCE_MERGED, (payload) => {
    const parsed = parseSentenceMergedPayload(payload)
    if (parsed) {
      handlers.onSentenceMerged(parsed)
    }
  })

  const unbindSentenceClipped = on(SENTENCE_CLIPPED, (payload) => {
    const parsed = parseSentenceClippedPayload(payload)
    if (parsed) {
      handlers.onSentenceClipped(parsed)
    }
  })

  return [
    unbindProcessingCreated,
    unbindProcessingUpdated,
    unbindSentenceListRebuilt,
    unbindSentenceMerged,
    unbindSentenceClipped,
  ]
}
