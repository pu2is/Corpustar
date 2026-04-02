import { defineStore } from 'pinia'

import { post } from '@/stores/fetchWrapper'
import { on } from '@/socket/socket'
import type { ProcessResponseWithId } from '@/types/general'
import type {
  CollectSentenceRequest,
  CorrectSentenceRequest,
  SentenceClipRequest,
  SentenceClippedSocketPayload,
  SentenceCursorPage,
  SentenceItem,
  SentenceMergeRequest,
  SentenceMergedSocketPayload,
} from '@/types/sentences'

const SENTENCE_ITEM_PER_PAGE = Number.parseInt(import.meta.env.VITE_SENTENCE_ITEM_PER_PAGE ?? '10', 10)

export const useSentenceStore = defineStore('sentence-store', {
  state: () => ({
    sentences: [] as SentenceItem[],
    connected: false as boolean,
  }),
  getters: {
    findSentenceById:
      (state) =>
      (sentenceId: string): SentenceItem | null =>
        state.sentences.find((item) => item.id === sentenceId) ?? null,

    getSentenceItems:
      (state) =>
      (docId: string, segmentationId: string): SentenceItem[] =>
        state.sentences.filter((item) => item.doc_id === docId && item.version_id === segmentationId),
  },
  actions: {
    // 1. Socket binding
    bindSocketEvents(): void {
      if (this.connected) {
        return
      }

      on('socket:connected', () => {
        this.connected = true
      })
      on('socket:disconnected', () => {
        this.connected = false
      })
      on('sentence:merged', (socketMsg) => {
        const payload = socketMsg as SentenceMergedSocketPayload
        const sentenceIds = payload?.meta?.sentence_ids ?? []
        const mergedSentence = payload?.result

        if (!mergedSentence || sentenceIds.length === 0) {
          return
        }

        const originalInsertIndex = this.sentences.findIndex((item) => sentenceIds.includes(item.id))
        this.sentences = this.sentences.filter((item) => !sentenceIds.includes(item.id))
        if (originalInsertIndex >= 0) {
          this.sentences.splice(originalInsertIndex, 0, mergedSentence)
          return
        }

        this.sentences.unshift(mergedSentence)
      })
      on('sentence:clipped', (socketMsg) => {
        const payload = socketMsg as SentenceClippedSocketPayload
        const sentenceId = payload?.meta?.sentence_id ?? ''
        const clippedItems = payload?.result ?? []
        if (!sentenceId || clippedItems.length === 0) {
          return
        }

        const clippedIndex = this.sentences.findIndex((item) => item.id === sentenceId)
        if (clippedIndex >= 0) {
          this.sentences.splice(clippedIndex, 1, ...clippedItems)
          return
        }

        this.sentences.push(...clippedItems)
      })
      on('sentence:corrected', (socketMsg) => {
        const payload = socketMsg as SentenceItem
        const sentenceIndex = this.sentences.findIndex((item) => item.id === payload.id)
        if (sentenceIndex >= 0) {
          this.sentences.splice(sentenceIndex, 1, payload)
        }
      })
      on('segmentation:succeed', (socketMsg) => {
        const previewItems = (socketMsg as { preview?: SentenceItem[] })?.preview ?? []
        this.sentences = previewItems
      })
    },

    // 2. API requests
    async getSentences(docId: string, segmentationId: string, splitOffset: number | null = null,
      limit = SENTENCE_ITEM_PER_PAGE, saveToStore = true): Promise<SentenceCursorPage> {
      const requestPayload: CollectSentenceRequest = {
        doc_id: docId,
        segmentation_id: segmentationId,
        split_offset: splitOffset,
        limit,
      }
      const items = await post<SentenceItem[]>('/api/sentences', requestPayload)
      if (saveToStore) {
        this.sentences = items
      }
      const hasMore = items.length === limit
      const nextAfterStartOffset = hasMore ? items[items.length - 1]?.start_offset ?? null : null
      return { items, next_after_start_offset: nextAfterStartOffset, has_more: hasMore}
    },

    async mergeSentences(sentenceIds: string[]): Promise<ProcessResponseWithId> {
      const payload: SentenceMergeRequest = { sentence_ids: sentenceIds }
      return post<ProcessResponseWithId>('/api/sentence/merge', payload)
    },

    async clipSentence(sentenceId: string, splitOffset: number): Promise<ProcessResponseWithId> {
      const payload: SentenceClipRequest = {
        sentence_id: sentenceId,
        split_offset: splitOffset,
      }
      return post<ProcessResponseWithId>('/api/sentence/clip', payload)
    },

    async correctSentence(sentenceId: string, correctedText: string): Promise<ProcessResponseWithId> {
      const payload: CorrectSentenceRequest = {
        sentence_id: sentenceId,
        corrected_text: correctedText,
      }
      return post<ProcessResponseWithId>('/api/sentence/correct', payload)
    },

    // 3. Helpers
    upsertSentence(sentence: SentenceItem): void {
      const existingIndex = this.sentences.findIndex((item) => item.id === sentence.id)
      if (existingIndex >= 0) {
        this.sentences.splice(existingIndex, 1, sentence)
        return
      }

      this.sentences.push(sentence)
    },
  },
})
