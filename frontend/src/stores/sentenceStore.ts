import { defineStore } from 'pinia'
import { get, post } from '@/stores/fetchWrapper'
import { on } from '@/socket/socket'
import type { ClipSentenceResponse, SentenceCursorPage, SentenceItem} from '@/types/sentences'

export type SentenceDisplayType = 'source' | 'lemma'

function getSentencePageKey(docId: string, processId: string): string {
  return `${docId}::${processId}`
}

export const useSentenceStore = defineStore('sentence-store', {
  state: () => ({
    sentences: [] as SentenceItem[],
    connected: false as boolean,
    displayType: null as SentenceDisplayType | null,
    pageStateByDocProcessKey: {} as Record<string, { offset: number | null, limit: number }>,
  }),
  getters: {
    getSentenceItems: (state) => (docId: string, processId: string): SentenceItem[] => {
      if (!docId || !processId) {
        return []
      }

      return state.sentences.filter((sentence) => (
        sentence.docId === docId && sentence.processingId === processId
      ))
    },
  },
  actions: {
    bindSocketEvents(): void {
      if (this.connected) {
        return
      }

      on('sentence:merged', (socketMsg) => {
        const sentence = socketMsg as SentenceItem
        if (!sentence?.docId || !sentence?.processingId) {
          return
        }

        void this.refreshLoadedSentences(sentence.docId, sentence.processingId).catch(() => undefined)
      })
      on('sentence:clipped', (socketMsg) => {
        const firstSentence = (socketMsg as SentenceItem[])?.[0]
        if (!firstSentence?.docId || !firstSentence?.processingId) {
          return
        }

        void this.refreshLoadedSentences(firstSentence.docId, firstSentence.processingId).catch(() => undefined)
      })
      this.connected = true
    },

    // Get
    async getSentences(docId: string, processId: string,
      offset: number | null = null, limit?: number,
      saveToStore = true): Promise<SentenceCursorPage> {
      const resolvedLimit = limit ?? Number.parseInt(import.meta.env.VITE_SENTENCE_ITEM_PER_PAGE ?? '10')
      const page = await get<SentenceCursorPage>(
        `/api/sentences/${encodeURIComponent(docId)}`,
        {
          params: {
            processingId: processId,
            afterStartOffset: offset,
            limit: resolvedLimit,
          },
        },
      )

      if (saveToStore) {
        const pageKey = getSentencePageKey(docId, processId)
        this.pageStateByDocProcessKey[pageKey] = {
          offset,
          limit: resolvedLimit,
        }
        this.sentences = page.items ?? []
      }

      return page
    },

    // Post: merge
    async mergeSentences(sentenceIds: string[]): Promise<SentenceItem> {
      const normalizedSentenceIds = [...new Set(sentenceIds.filter((sentenceId) => sentenceId))]
      if (normalizedSentenceIds.length < 2) {
        throw new Error('At least two sentence IDs are required for merge.')
      }

      const mergedItem = await post<SentenceItem>('/api/sentences/merge', {
        sentenceIds: normalizedSentenceIds,
      })
      return mergedItem
    },

    // Post: clip
    async clipSentence(sentenceId: string, splitOffset: number): Promise<SentenceItem[]> {
      const response = await post<ClipSentenceResponse>(
        `/api/sentences/${encodeURIComponent(sentenceId)}/clip`,
        { splitOffset },
      )
      return response.items ?? []
    },

    async refreshLoadedSentences(docId: string, processId: string): Promise<SentenceCursorPage> {
      const pageKey = getSentencePageKey(docId, processId)
      const existingItems = this.sentences.filter((sentence) => (
        sentence.docId === docId && sentence.processingId === processId
      ))
      const trackedPageState = this.pageStateByDocProcessKey[pageKey]
      const limit = trackedPageState?.limit
        ?? Math.max(existingItems.length, Number.parseInt(import.meta.env.VITE_SENTENCE_ITEM_PER_PAGE ?? '10'))
      const offset = trackedPageState?.offset ?? null
      this.sentences = []
      return this.getSentences(docId, processId, offset, limit)
    },

    // Sentence Table Display
    resetDisplayType(): void {
      this.displayType = null
    },

    ensureDisplayType(processItemCount: number): void {
      if (processItemCount  < 2) {
        this.displayType = null
        return
      }

      if (this.displayType === null) {
        this.displayType = 'source'
      }
    },

    toggleDisplayType(): void {
      if (this.displayType === null) {
        return
      }

      this.displayType = this.displayType === 'source' ? 'lemma' : 'source'
    },
  },
})
