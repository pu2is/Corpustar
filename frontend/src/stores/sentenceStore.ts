import { defineStore } from 'pinia';

import {
  clipSentence as clipSentenceApi,
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
  SentenceSegmentationResponse,
} from '@/types/sentences'

interface SentenceState {
  processingByDocId: Record<string, ProcessingItem | null>
  itemsByDocId: Record<string, SentenceItem[]>
  nextAfterStartOffsetByDocId: Record<string, number | null>
  hasMoreByDocId: Record<string, boolean>
  loadingByDocId: Record<string, boolean>
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
): ProcessingItem {
  const nowIso = new Date().toISOString()
  const fallbackState: ProcessingState = existing?.state ?? 'running'

  return {
    id: payload.processingId,
    docId: payload.docId,
    type: existing?.type ?? 'sentence_segmentation',
    state: toProcessingState(payload.state, fallbackState),
    createdAt: existing?.createdAt ?? nowIso,
    updatedAt: nowIso,
    errorMessage: payload.errorMessage ?? existing?.errorMessage ?? null,
    meta: existing?.meta ?? null,
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

export const useSentenceStore = defineStore('sentence-store', {
  state: (): SentenceState => ({
    processingByDocId: {},
    itemsByDocId: {},
    nextAfterStartOffsetByDocId: {},
    hasMoreByDocId: {},
    loadingByDocId: {},
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

    handleProcessingCreated(payload: ProcessingEventPayload): void {
      this.processingByDocId[payload.docId] = buildProcessingFromEvent(
        this.processingByDocId[payload.docId],
        payload,
      )
    },

    handleProcessingUpdated(payload: ProcessingEventPayload): void {
      this.processingByDocId[payload.docId] = buildProcessingFromEvent(
        this.processingByDocId[payload.docId],
        payload,
      )
    },

    handleSentenceListRebuilt(payload: SentenceListRebuiltPayload): void {
      this.refreshActiveSentenceList(payload.docId, payload.processingId)
    },

    handleSentenceMerged(payload: SentenceMergedPayload): void {
      this.refreshActiveSentenceList(payload.docId, payload.processingId)
    },

    handleSentenceClipped(payload: SentenceClippedPayload): void {
      this.refreshActiveSentenceList(payload.docId, payload.processingId)
    },

    refreshActiveSentenceList(docId: string, processingId: string): void {
      const activeProcessing = this.processingByDocId[docId]
      if (!activeProcessing || activeProcessing.id !== processingId) {
        return
      }
      if (this.loadingByDocId[docId]) {
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

    async segmentDocument(docId: string): Promise<SentenceSegmentationResponse> {
      this.loadingByDocId[docId] = true
      this.errorByDocId[docId] = null

      try {
        const response = await segmentDocumentSentences(docId)
        const preview = response.preview ?? []
        const hasMore = response.sentenceCount > preview.length
        const lastSentence = preview.length ? preview[preview.length - 1] : null

        this.processingByDocId[docId] = response.processing
        this.itemsByDocId[docId] = preview
        this.nextAfterStartOffsetByDocId[docId] = hasMore && lastSentence
          ? lastSentence.startOffset
          : null
        this.hasMoreByDocId[docId] = hasMore
        this.selectedSentenceIdsByDocId[docId] = []

        return response
      } catch (error) {
        this.errorByDocId[docId] = toErrorMessage(error)
        throw error
      } finally {
        this.loadingByDocId[docId] = false
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
      }
    },
  },
});
