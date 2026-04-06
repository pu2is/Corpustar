import { defineStore } from 'pinia'

import { post } from '@/stores/fetchWrapper'
import { on } from '@/socket/socket'
import type { ProcessResponseWithId } from '@/types/general'
import type { CollectSentenceRequest, SentenceItem, SentenceListItem} from '@/types/sentences'

const SENTENCE_ITEM_PER_PAGE = Number.parseInt(import.meta.env.VITE_SENTENCE_ITEM_PER_PAGE ?? '10', 10)

export const useSentenceStore = defineStore('sentence-store', {
  state: () => ({
    sentenceList: { 
      prevSentence: null,
      sentences: [],
      cursor: {
        currentCursor: null,
        nextCursor: null,
        prevCursor: null,
      },
      highlight: [],
    } as SentenceListItem,
    connected: false as boolean,
  }),
  getters: {
    sentences: (state): SentenceItem[] => state.sentenceList.sentences,

    findSentenceById: (state) =>
      (sentenceId: string): SentenceItem | null =>
        state.sentenceList.sentences.find((item) => item.id === sentenceId) ?? null,

    getSentenceItems: (state) =>
      (docId: string, segmentationId: string): SentenceItem[] =>
        state.sentenceList.sentences.filter(
          (item) => item.doc_id === docId && item.version_id === segmentationId,
        ),
    getSentenceLengthBySegmentationId: (state) =>
      (segmentationId: string): number =>
        state.sentenceList.sentences.filter((item) => item.version_id === segmentationId).length,
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
        this.sentenceList = socketMsg as SentenceListItem
      })
      on('sentence:clipped', (socketMsg) => {
        this.sentenceList = socketMsg as SentenceListItem
      })
      on('sentence:corrected', (socketMsg) => {
        this.sentenceList = socketMsg as SentenceListItem
      })
      on('segmentation:succeed', (socketMsg) => {
        const payload = socketMsg as { preview: SentenceListItem }
        this.sentenceList = payload.preview
      })
    },

    // Post: collect sentences
    async getSentences(docId: string, segmentationId: string, cursor: string | null = null,
      limit = SENTENCE_ITEM_PER_PAGE, saveToStore = true): Promise<SentenceListItem> {
      const requestPayload: CollectSentenceRequest = { doc_id: docId, segmentation_id: segmentationId,
        cursor, limit }
      const response = await post<SentenceListItem>('/api/sentences', requestPayload)
      const sentenceList = response
      if (saveToStore) {
        this.sentenceList = sentenceList
      }

      return sentenceList
    },

    // Post: merge
    async mergeSentences(sentenceIds: string[]): Promise<ProcessResponseWithId> {
      return post<ProcessResponseWithId>('/api/sentence/merge', {
        sentence_ids: sentenceIds, limit:  SENTENCE_ITEM_PER_PAGE,
      })
    },

    // Post: clip
    async clipSentence(sentenceId: string, splitOffset: number): Promise<ProcessResponseWithId> {
      return post<ProcessResponseWithId>('/api/sentence/clip', { sentence_id: sentenceId,
        split_offset: splitOffset, limit: SENTENCE_ITEM_PER_PAGE })
    },

    // Post: correct
    async correctSentence(sentenceId: string, correctedText: string): Promise<ProcessResponseWithId> {
      return post<ProcessResponseWithId>('/api/sentence/correct', {
        sentence_id: sentenceId, corrected_text: correctedText,
        cursor: this.sentenceList.cursor.currentCursor, limit: SENTENCE_ITEM_PER_PAGE,
      })
    },
  }
})
