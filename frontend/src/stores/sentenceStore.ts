import { defineStore } from 'pinia';

import {
  clipSentence as clipSentenceApi,
  getLatestSentenceSegmentationResult,
  getSentenceCursorPage as getSentenceCursorPageApi,
  mergeSentences,
  segmentDocumentSentences,
} from '@/api/sentenceApi'
import {
  bindSentenceSocketHandlers,
  type ProcessingEventPayload,
  type SentenceClippedPayload,
  type SentenceListRebuiltPayload,
  type SentenceMergedPayload,
} from '@/socket/sentenceSocket'
import type { ProcessingItem, ProcessingState } from '@/types/processings'
import type {
  SentenceCursorPage,
  SentenceItem,
  SentenceSegmentationResultSnapshot,
  SentenceSegmentationResponse,
} from '@/types/sentences'

interface SentenceState {
  processingByDocId: Record<string, ProcessingItem | null>
  itemsByDocId: Record<string, SentenceItem[]>
  nextAfterStartOffsetByDocId: Record<string, number | null>
  hasMoreByDocId: Record<string, boolean>
  loadingByDocId: Record<string, boolean>
  pendingRefreshProcessingIdByDocId: Record<string, string | null>
  selectedSentenceIdsByDocId: Record<string, string[]>
  errorByDocId: Record<string, string | null>
}

const DEFAULT_SENTENCE_PAGE_LIMIT = 20
const PROCESSING_STATE_SET = new Set<ProcessingState>(['running', 'succeed', 'failed'])
let socketBound = false
let socketUnsubscribers: Array<() => void> = []

function toErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

function toProcessingState(
  candidate: string | undefined,
  fallback: ProcessingState,
): ProcessingState {
  if (candidate && PROCESSING_STATE_SET.has(candidate as ProcessingState)) {
    return candidate as ProcessingState
  }
  return fallback
}

function buildProcessingFromEvent(
  existing: ProcessingItem | null | undefined,
  payload: ProcessingEventPayload,
  options?: {
    fallbackState?: ProcessingState
  },
): ProcessingItem {
  const nowIso = new Date().toISOString()
  const isSameProcessing = existing?.id === payload.processingId
  const fallbackState: ProcessingState = options?.fallbackState
    ?? (isSameProcessing ? (existing?.state ?? 'running') : 'running')

  return {
    id: payload.processingId,
    docId: payload.docId,
    type: isSameProcessing ? (existing?.type ?? 'sentence_segmentation') : 'sentence_segmentation',
    state: toProcessingState(payload.state, fallbackState),
    createdAt: isSameProcessing ? (existing?.createdAt ?? nowIso) : nowIso,
    updatedAt: nowIso,
    errorMessage: payload.errorMessage !== undefined
      ? payload.errorMessage
      : (isSameProcessing ? (existing?.errorMessage ?? null) : null),
    meta: isSameProcessing ? (existing?.meta ?? null) : null,
  }
}

function uniqueNonEmptySentenceIds(sentenceIds: string[]): string[] {
  const seen = new Set<string>()
  const normalized: string[] = []

  for (const sentenceId of sentenceIds) {
    if (!sentenceId || seen.has(sentenceId)) {
      continue
    }

    seen.add(sentenceId)
    normalized.push(sentenceId)
  }

  return normalized
}

function hasOwnRecord(record: Record<string, unknown>, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(record, key)
}

function getNextAfterStartOffsetFromPreview(
  preview: SentenceItem[],
  hasMore: boolean,
): number | null {
  if (!hasMore || !preview.length) {
    return null
  }
  return preview[preview.length - 1].startOffset
}

export const useSentenceStore = defineStore('sentence-store', {
  state: (): SentenceState => ({
    processingByDocId: {},
    itemsByDocId: {},
    nextAfterStartOffsetByDocId: {},
    hasMoreByDocId: {},
    loadingByDocId: {},
    pendingRefreshProcessingIdByDocId: {},
    selectedSentenceIdsByDocId: {},
    errorByDocId: {},
  }),
  actions: {
    bindSocketEvents(): void {
      if (socketBound) {
        return
      }

      socketUnsubscribers = bindSentenceSocketHandlers(
        {
          onProcessingCreated: (payload) => {
            this.handleProcessingCreated(payload)
          },
          onProcessingUpdated: (payload) => {
            this.handleProcessingUpdated(payload)
          },
          onSentenceListRebuilt: (payload) => {
            this.handleSentenceListRebuilt(payload)
          },
          onSentenceMerged: (payload) => {
            this.handleSentenceMerged(payload)
          },
          onSentenceClipped: (payload) => {
            this.handleSentenceClipped(payload)
          },
        },
      )
      socketBound = true
    },

    unbindSocketEvents(): void {
      for (const unsubscribe of socketUnsubscribers) {
        unsubscribe()
      }
      socketUnsubscribers = []
      socketBound = false
    },

    isDocTracked(docId: string): boolean {
      return hasOwnRecord(this.processingByDocId, docId)
        || hasOwnRecord(this.itemsByDocId, docId)
    },

    setActiveProcessingFromEvent(
      payload: ProcessingEventPayload,
      options?: {
        fallbackState?: ProcessingState
      },
    ): void {
      this.processingByDocId[payload.docId] = buildProcessingFromEvent(
        this.processingByDocId[payload.docId],
        payload,
        options,
      )
    },

    queueSentenceListRefresh(docId: string, processingId: string): void {
      this.pendingRefreshProcessingIdByDocId[docId] = processingId
    },

    flushQueuedSentenceListRefresh(docId: string): void {
      if (this.loadingByDocId[docId]) {
        return
      }

      const pendingProcessingId = this.pendingRefreshProcessingIdByDocId[docId]
      if (!pendingProcessingId) {
        return
      }

      this.pendingRefreshProcessingIdByDocId[docId] = null
      this.setActiveProcessingFromEvent(
        {
          docId,
          processingId: pendingProcessingId,
          state: 'succeed',
          errorMessage: null,
        },
        {
          fallbackState: 'succeed',
        },
      )
      void this.loadInitialSentences(docId, pendingProcessingId).catch(() => undefined)
    },

    handleProcessingCreated(payload: ProcessingEventPayload): void {
      this.setActiveProcessingFromEvent(
        {
          ...payload,
          state: payload.state ?? 'running',
          errorMessage: payload.errorMessage ?? null,
        },
        {
          fallbackState: 'running',
        },
      )
    },

    handleProcessingUpdated(payload: ProcessingEventPayload): void {
      this.setActiveProcessingFromEvent(payload)
    },

    handleSentenceListRebuilt(payload: SentenceListRebuiltPayload): void {
      if (!this.isDocTracked(payload.docId)) {
        return
      }

      this.setActiveProcessingFromEvent(
        {
          docId: payload.docId,
          processingId: payload.processingId,
          state: 'succeed',
          errorMessage: null,
        },
        {
          fallbackState: 'succeed',
        },
      )

      if (this.loadingByDocId[payload.docId]) {
        this.queueSentenceListRefresh(payload.docId, payload.processingId)
        return
      }

      void this.loadInitialSentences(payload.docId, payload.processingId).catch(() => undefined)
    },

    handleSentenceMerged(payload: SentenceMergedPayload): void {
      this.refreshActiveSentenceList(payload.docId, payload.processingId)
    },

    handleSentenceClipped(payload: SentenceClippedPayload): void {
      this.refreshActiveSentenceList(payload.docId, payload.processingId)
    },

    refreshActiveSentenceList(docId: string, processingId: string): void {
      const activeProcessing = this.processingByDocId[docId]
      const isDocTracked = this.isDocTracked(docId)

      if (!activeProcessing) {
        if (!isDocTracked || this.loadingByDocId[docId]) {
          return
        }
        void this.initializeAnalyzePage(docId).catch(() => undefined)
        return
      }

      if (activeProcessing.id !== processingId) {
        return
      }
      if (this.loadingByDocId[docId]) {
        this.queueSentenceListRefresh(docId, processingId)
        return
      }

      void this.loadInitialSentences(docId, processingId).catch(() => undefined)
    },

    resetDocSentenceState(docId: string): void {
      this.processingByDocId[docId] = null
      this.itemsByDocId[docId] = []
      this.nextAfterStartOffsetByDocId[docId] = null
      this.hasMoreByDocId[docId] = false
      this.loadingByDocId[docId] = false
      this.pendingRefreshProcessingIdByDocId[docId] = null
      this.selectedSentenceIdsByDocId[docId] = []
      this.errorByDocId[docId] = null
    },

    setSelectedSentenceIds(docId: string, sentenceIds: string[]): void {
      this.selectedSentenceIdsByDocId[docId] = uniqueNonEmptySentenceIds(sentenceIds)
    },

    toggleSentenceSelection(docId: string, sentenceId: string): void {
      if (!sentenceId) {
        return
      }

      const current = this.selectedSentenceIdsByDocId[docId] ?? []
      if (current.includes(sentenceId)) {
        this.selectedSentenceIdsByDocId[docId] = current.filter((id) => id !== sentenceId)
        return
      }

      this.selectedSentenceIdsByDocId[docId] = [...current, sentenceId]
    },

    clearSelection(docId: string): void {
      this.selectedSentenceIdsByDocId[docId] = []
    },

    applySegmentationSnapshot(
      docId: string,
      response: SentenceSegmentationResultSnapshot,
    ): void {
      const preview = response.preview ?? []
      const hasMore = response.sentenceCount > preview.length

      this.processingByDocId[docId] = response.processing
      this.itemsByDocId[docId] = preview
      this.nextAfterStartOffsetByDocId[docId] = getNextAfterStartOffsetFromPreview(
        preview,
        hasMore,
      )
      this.hasMoreByDocId[docId] = hasMore
      this.pendingRefreshProcessingIdByDocId[docId] = null
      this.selectedSentenceIdsByDocId[docId] = []
    },

    async initializeAnalyzePage(docId: string): Promise<SentenceSegmentationResultSnapshot> {
      this.processingByDocId[docId] = null
      this.itemsByDocId[docId] = []
      this.nextAfterStartOffsetByDocId[docId] = null
      this.hasMoreByDocId[docId] = false
      this.pendingRefreshProcessingIdByDocId[docId] = null
      this.selectedSentenceIdsByDocId[docId] = []
      this.errorByDocId[docId] = null
      this.loadingByDocId[docId] = true

      try {
        const response = await getLatestSentenceSegmentationResult(docId)
        this.applySegmentationSnapshot(docId, response)
        return response
      } catch (error) {
        this.errorByDocId[docId] = toErrorMessage(error)
        throw error
      } finally {
        this.loadingByDocId[docId] = false
        this.flushQueuedSentenceListRefresh(docId)
      }
    },

    async segmentDocument(docId: string): Promise<SentenceSegmentationResponse> {
      this.loadingByDocId[docId] = true
      this.errorByDocId[docId] = null

      try {
        const response = await segmentDocumentSentences(docId)
        this.processingByDocId[docId] = response.processing
        this.selectedSentenceIdsByDocId[docId] = []

        if (response.processing.state === 'succeed') {
          this.applySegmentationSnapshot(docId, response)
        }

        return response
      } catch (error) {
        this.errorByDocId[docId] = toErrorMessage(error)
        throw error
      } finally {
        this.loadingByDocId[docId] = false
        this.flushQueuedSentenceListRefresh(docId)
      }
    },

    async loadInitialSentences(docId: string, processingId: string): Promise<SentenceCursorPage> {
      this.loadingByDocId[docId] = true
      this.errorByDocId[docId] = null

      try {
        const page = await getSentenceCursorPageApi(
          docId,
          processingId,
          null,
          DEFAULT_SENTENCE_PAGE_LIMIT,
        )
        this.itemsByDocId[docId] = page.items ?? []
        this.nextAfterStartOffsetByDocId[docId] = page.nextAfterStartOffset
        this.hasMoreByDocId[docId] = page.hasMore
        this.selectedSentenceIdsByDocId[docId] = []
        return page
      } catch (error) {
        this.errorByDocId[docId] = toErrorMessage(error)
        throw error
      } finally {
        this.loadingByDocId[docId] = false
        this.flushQueuedSentenceListRefresh(docId)
      }
    },

    async loadMoreSentences(docId: string, processingId: string): Promise<SentenceCursorPage | null> {
      if (!this.hasMoreByDocId[docId]) {
        return null
      }

      this.loadingByDocId[docId] = true
      this.errorByDocId[docId] = null

      try {
        const page = await getSentenceCursorPageApi(
          docId,
          processingId,
          this.nextAfterStartOffsetByDocId[docId] ?? null,
          DEFAULT_SENTENCE_PAGE_LIMIT,
        )

        const existingItems = this.itemsByDocId[docId] ?? []
        const existingIds = new Set(existingItems.map((item) => item.id))
        const newItems = (page.items ?? []).filter((item) => !existingIds.has(item.id))

        this.itemsByDocId[docId] = [...existingItems, ...newItems]
        this.nextAfterStartOffsetByDocId[docId] = page.nextAfterStartOffset
        this.hasMoreByDocId[docId] = page.hasMore

        return page
      } catch (error) {
        this.errorByDocId[docId] = toErrorMessage(error)
        throw error
      } finally {
        this.loadingByDocId[docId] = false
        this.flushQueuedSentenceListRefresh(docId)
      }
    },

    async mergeSelected(docId: string): Promise<void> {
      const processing = this.processingByDocId[docId]
      if (!processing) {
        throw new Error(`No processing found for document: ${docId}`)
      }

      const selectedSentenceIds = uniqueNonEmptySentenceIds(
        this.selectedSentenceIdsByDocId[docId] ?? [],
      )
      if (!selectedSentenceIds.length) {
        return
      }

      this.loadingByDocId[docId] = true
      this.errorByDocId[docId] = null

      try {
        await mergeSentences(selectedSentenceIds)
        await this.loadInitialSentences(docId, processing.id)
      } catch (error) {
        this.errorByDocId[docId] = toErrorMessage(error)
        throw error
      } finally {
        this.loadingByDocId[docId] = false
        this.flushQueuedSentenceListRefresh(docId)
      }
    },

    async clipSentence(docId: string, sentenceId: string, splitOffset: number): Promise<void> {
      const processing = this.processingByDocId[docId]
      if (!processing) {
        throw new Error(`No processing found for document: ${docId}`)
      }

      this.loadingByDocId[docId] = true
      this.errorByDocId[docId] = null

      try {
        await clipSentenceApi(sentenceId, splitOffset)
        await this.loadInitialSentences(docId, processing.id)
      } catch (error) {
        this.errorByDocId[docId] = toErrorMessage(error)
        throw error
      } finally {
        this.loadingByDocId[docId] = false
        this.flushQueuedSentenceListRefresh(docId)
      }
    },
  },
});
