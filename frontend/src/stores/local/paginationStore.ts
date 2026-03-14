import { defineStore } from 'pinia'

import { useSentenceStore } from '@/stores/sentenceStore'
import type { SentenceCursorPage } from '@/types/sentences'

interface PaginationProgress {
  nextAfterStartOffset: number | null
  hasMore: boolean
  limit: number
}

interface PaginationState {
  progressByDocProcessKey: Record<string, PaginationProgress>
  loadingByDocProcessKey: Record<string, boolean>
  errorByDocProcessKey: Record<string, string | null>
}

const DEFAULT_SENTENCE_PAGE_LIMIT = 20

function toErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

function getPaginationKey(docId: string, processId: string): string {
  return `${docId}::${processId}`
}

export const usePaginationStore = defineStore('pagination-store', {
  state: (): PaginationState => ({
    progressByDocProcessKey: {},
    loadingByDocProcessKey: {},
    errorByDocProcessKey: {},
  }),
  getters: {
    hasMore: (state) => (docId: string, processId: string): boolean => {
      if (!docId || !processId) {
        return false
      }

      const key = getPaginationKey(docId, processId)
      return state.progressByDocProcessKey[key]?.hasMore ?? false
    },
    isLoading: (state) => (docId: string, processId: string): boolean => {
      if (!docId || !processId) {
        return false
      }

      const key = getPaginationKey(docId, processId)
      return state.loadingByDocProcessKey[key] ?? false
    },
  },
  actions: {
    ensureProgress(docId: string, processId: string, limit = DEFAULT_SENTENCE_PAGE_LIMIT): PaginationProgress {
      const key = getPaginationKey(docId, processId)
      if (!this.progressByDocProcessKey[key]) {
        this.progressByDocProcessKey[key] = {
          nextAfterStartOffset: null,
          hasMore: false,
          limit,
        }
      }
      return this.progressByDocProcessKey[key]
    },

    applyPage(
      docId: string,
      processId: string,
      page: SentenceCursorPage,
      limit: number,
    ): void {
      const key = getPaginationKey(docId, processId)
      this.progressByDocProcessKey[key] = {
        nextAfterStartOffset: page.nextAfterStartOffset,
        hasMore: page.hasMore,
        limit,
      }
    },

    async loadFirstPage(
      docId: string,
      processId: string,
      limit = DEFAULT_SENTENCE_PAGE_LIMIT,
    ): Promise<SentenceCursorPage> {
      const key = getPaginationKey(docId, processId)
      const sentenceStore = useSentenceStore()
      this.loadingByDocProcessKey[key] = true
      this.errorByDocProcessKey[key] = null

      try {
        const page = await sentenceStore.getSentences(docId, processId, {
          afterStartOffset: null,
          limit,
          append: false,
        })
        this.applyPage(docId, processId, page, limit)
        return page
      } catch (error) {
        this.errorByDocProcessKey[key] = toErrorMessage(error)
        throw error
      } finally {
        this.loadingByDocProcessKey[key] = false
      }
    },

    async loadMore(docId: string, processId: string): Promise<SentenceCursorPage | null> {
      const key = getPaginationKey(docId, processId)
      const sentenceStore = useSentenceStore()
      const progress = this.ensureProgress(docId, processId)
      if (!progress.hasMore) {
        return null
      }

      this.loadingByDocProcessKey[key] = true
      this.errorByDocProcessKey[key] = null

      try {
        const page = await sentenceStore.getSentences(docId, processId, {
          afterStartOffset: progress.nextAfterStartOffset,
          limit: progress.limit,
          append: true,
        })
        this.applyPage(docId, processId, page, progress.limit)
        return page
      } catch (error) {
        this.errorByDocProcessKey[key] = toErrorMessage(error)
        throw error
      } finally {
        this.loadingByDocProcessKey[key] = false
      }
    },
  },
})
