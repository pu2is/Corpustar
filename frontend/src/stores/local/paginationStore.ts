import { defineStore } from 'pinia'
import { useSentenceStore } from '@/stores/sentenceStore'

export type SentenceAnchorMap = Record<string, string>

interface SentencePaginationEntry {
  currentPage: number
  offsets: Array<number | null>
  hasMore: boolean
  nextAfterStartOffset: number | null
  loading: boolean
  processingId: string
}

const SENTENCE_ITEM_PER_PAGE = Number.parseInt(import.meta.env.VITE_SENTENCE_ITEM_PER_PAGE ?? '10', 10)
const SENTENCE_ANCHOR_STORAGE_KEY = 'corpustar.sentence-anchors'

function createEntry(processingId = ''): SentencePaginationEntry {
  return {
    currentPage: 1,
    offsets: [null],
    hasMore: false,
    nextAfterStartOffset: null,
    loading: false,
    processingId,
  }
}

function readSentenceAnchors(): SentenceAnchorMap {
  if (typeof window === 'undefined') {
    return {}
  }

  try {
    return JSON.parse(window.localStorage.getItem(SENTENCE_ANCHOR_STORAGE_KEY) ?? '{}') as SentenceAnchorMap
  } catch {
    return {}
  }
}

export const usePaginationStore = defineStore('pagination-store', {
  state: () => ({
    sentenceAnchors: {} as SentenceAnchorMap,
    paginationByDocId: {} as Record<string, SentencePaginationEntry>,
    hydrated: false,
  }),
  getters: {
    getSentenceAnchor: (state) => (docId: string): string | null => state.sentenceAnchors[docId] ?? null,
    getPaginationEntry: (state) => (docId: string): SentencePaginationEntry => state.paginationByDocId[docId] ?? createEntry(),
  },
  actions: {
    hydrateFromLocalStorage(): void {
      if (this.hydrated) {
        return
      }

      // Restore { [docId]: firstSentenceIdOfCurrentPage } from localStorage once.
      this.sentenceAnchors = readSentenceAnchors()
      this.hydrated = true
    },

    persist(): void {
      if (typeof window === 'undefined') {
        return
      }

      window.localStorage.setItem(SENTENCE_ANCHOR_STORAGE_KEY, JSON.stringify(this.sentenceAnchors))
    },

    entry(docId: string, processingId = ''): SentencePaginationEntry {
      const current = this.paginationByDocId[docId]
      if (!current || (processingId && current.processingId !== processingId)) {
        const next = createEntry(processingId)
        this.paginationByDocId[docId] = next
        return next
      }

      return current
    },

    saveAnchor(docId: string, sentenceId: string | null): void {
      // Save the first sentence id of the current page as the resume point for this document.
      if (!sentenceId) {
        delete this.sentenceAnchors[docId]
      } else {
        this.sentenceAnchors[docId] = sentenceId
      }

      this.persist()
    },

    async loadPage(docId: string, processingId: string,
      offset: number | null, pageNumber: number,
      offsets: Array<number | null>): Promise<void> {
      const entry = this.entry(docId, processingId)
      const sentenceStore = useSentenceStore()
      entry.loading = true

      try {
        // Ask backend for one page, then update page state and save progress locally.
        const page = await sentenceStore.getSentences(docId, processingId, offset, SENTENCE_ITEM_PER_PAGE)
        entry.currentPage = pageNumber
        entry.offsets = offsets
        entry.hasMore = page.hasMore
        entry.nextAfterStartOffset = page.nextAfterStartOffset ?? null
        entry.processingId = processingId
        this.saveAnchor(docId, page.items[0]?.id ?? null)
      } finally {
        entry.loading = false
      }
    },

    async restoreSavedPage(docId: string, processingId: string, anchorId: string): Promise<boolean> {
      const sentenceStore = useSentenceStore()
      let offset: number | null = null
      let pageNumber = 1
      let offsets: Array<number | null> = [null]

      while (true) {
        // Walk pages from the start until we find the saved first-sentence id.
        const page = await sentenceStore.getSentences(docId, processingId, offset, SENTENCE_ITEM_PER_PAGE, false)
        if (page.items[0]?.id === anchorId) {
          await this.loadPage(docId, processingId, offset, pageNumber, offsets)
          return true
        }

        if (!page.hasMore || page.nextAfterStartOffset === null) {
          return false
        }

        offset = page.nextAfterStartOffset
        pageNumber += 1
        offsets = [...offsets, offset]
      }
    },

    async initializeDocumentPagination(docId: string, processingId: string): Promise<void> {
      this.hydrateFromLocalStorage()
      this.entry(docId, processingId)

      const savedAnchor = this.getSentenceAnchor(docId)
      if (savedAnchor && await this.restoreSavedPage(docId, processingId, savedAnchor)) {
        return
      }

      await this.loadPage(docId, processingId, null, 1, [null])
    },

    async goToPreviousPage(docId: string, processingId: string): Promise<void> {
      const entry = this.entry(docId, processingId)
      if (entry.loading || entry.currentPage <= 1) {
        return
      }

      const previousPage = entry.currentPage - 1
      await this.loadPage(docId, processingId, entry.offsets[previousPage - 1] ?? null, previousPage, entry.offsets)
    },

    async goToNextPage(docId: string, processingId: string): Promise<void> {
      const entry = this.entry(docId, processingId)
      if (entry.loading || !entry.hasMore || entry.nextAfterStartOffset === null) {
        return
      }

      const nextPage = entry.currentPage + 1
      const nextOffsets = [...entry.offsets.slice(0, entry.currentPage), entry.nextAfterStartOffset]
      await this.loadPage(docId, processingId, entry.nextAfterStartOffset, nextPage, nextOffsets)
    },

    async refreshCurrentPage(docId: string, processingId: string): Promise<void> {
      const entry = this.entry(docId, processingId)
      await this.loadPage(docId, processingId, entry.offsets[entry.currentPage - 1] ?? null, entry.currentPage, entry.offsets)
    },
  },
})
