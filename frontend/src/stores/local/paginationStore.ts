import { defineStore } from 'pinia'
import { useSentenceStore } from '@/stores/sentenceStore'

export type SentenceAnchorMap = Record<string, string>

interface SentencePaginationEntry {
  currentPage: number
  offsets: Array<number | null>
  nextAfterStartOffset: number | null
  loading: boolean
  processingId: string
}

interface PaginationState {
  sentenceAnchors: SentenceAnchorMap
  paginationByDocId: Record<string, SentencePaginationEntry>
  hydrated: boolean
}

const SENTENCE_ITEM_PER_PAGE = Number.parseInt(import.meta.env.VITE_SENTENCE_ITEM_PER_PAGE ?? '10', 10)
const SENTENCE_ANCHOR_STORAGE_KEY = 'corpustar.sentence-anchors'

function createPaginationEntry(processingId = ''): SentencePaginationEntry {
  return {
    currentPage: 1,
    offsets: [null],
    nextAfterStartOffset: null,
    loading: false,
    processingId,
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function normalizeSentenceAnchorMap(value: unknown): SentenceAnchorMap {
  if (!isRecord(value)) {
    return {}
  }

  const normalized: SentenceAnchorMap = {}
  for (const [docId, sentenceId] of Object.entries(value)) {
    if (!docId || typeof sentenceId !== 'string' || !sentenceId.trim()) {
      continue
    }

    normalized[docId] = sentenceId
  }

  return normalized
}

export const usePaginationStore = defineStore('pagination-store', {
  state: (): PaginationState => ({
    sentenceAnchors: {},
    paginationByDocId: {},
    hydrated: false,
  }),
  getters: {
    getSentenceAnchor: (state) => (docId: string): string | null => {
      if (!docId) {
        return null
      }

      return state.sentenceAnchors[docId] ?? null
    },
    hasSentenceAnchor: (state) => (docId: string): boolean => {
      if (!docId) {
        return false
      }

      return Boolean(state.sentenceAnchors[docId])
    },
    getPaginationEntry: (state) => (docId: string): SentencePaginationEntry => {
      if (!docId) {
        return createPaginationEntry()
      }

      return state.paginationByDocId[docId] ?? createPaginationEntry()
    },
  },
  actions: {
    hydrateFromLocalStorage(): void {
      if (this.hydrated || typeof window === 'undefined') {
        this.hydrated = true
        return
      }

      try {
        const raw = window.localStorage.getItem(SENTENCE_ANCHOR_STORAGE_KEY)
        this.sentenceAnchors = raw ? normalizeSentenceAnchorMap(JSON.parse(raw)) : {}
      } catch {
        this.sentenceAnchors = {}
      } finally {
        this.hydrated = true
      }
    },

    persistSentenceAnchors(): void {
      if (typeof window === 'undefined') {
        return
      }

      window.localStorage.setItem(
        SENTENCE_ANCHOR_STORAGE_KEY,
        JSON.stringify(this.sentenceAnchors),
      )
    },

    ensurePaginationEntry(docId: string, processingId = ''): SentencePaginationEntry {
      const existingEntry = this.paginationByDocId[docId]
      if (existingEntry) {
        if (processingId && existingEntry.processingId !== processingId) {
          const nextEntry = createPaginationEntry(processingId)
          this.paginationByDocId[docId] = nextEntry
          return nextEntry
        }

        return existingEntry
      }

      const nextEntry = createPaginationEntry(processingId)
      this.paginationByDocId[docId] = nextEntry
      return nextEntry
    },

    setSentenceAnchor(docId: string, sentenceId: string | null): void {
      if (!docId) {
        return
      }

      if (!sentenceId) {
        delete this.sentenceAnchors[docId]
      } else {
        this.sentenceAnchors[docId] = sentenceId
      }

      this.persistSentenceAnchors()
    },

    rememberLoadedPage(docId: string, processingId: string,
      pageNumber: number, offsets: Array<number | null>,
      nextAfterStartOffset: number | null, firstSentenceId: string | null): void {
      const entry = this.ensurePaginationEntry(docId, processingId)
      entry.currentPage = pageNumber
      entry.offsets = offsets
      entry.nextAfterStartOffset = nextAfterStartOffset
      entry.processingId = processingId
      this.setSentenceAnchor(docId, firstSentenceId)
    },

    async loadPage(docId: string, processingId: string,
      offset: number | null, pageNumber: number,
      offsets: Array<number | null>): Promise<void> {
      if (!docId || !processingId) {
        return
      }

      const sentenceStore = useSentenceStore()
      const entry = this.ensurePaginationEntry(docId, processingId)
      entry.loading = true

      try {
        const page = await sentenceStore.getSentences(docId, processingId, offset, SENTENCE_ITEM_PER_PAGE)
        this.rememberLoadedPage(
          docId,
          processingId,
          pageNumber,
          offsets,
          page.nextAfterStartOffset ?? null,
          page.items[0]?.id ?? null,
        )
      } finally {
        entry.loading = false
      }
    },

    async restorePageByAnchor(docId: string, processingId: string, anchorId: string): Promise<boolean> {
      if (!docId || !processingId || !anchorId) {
        return false
      }

      const sentenceStore = useSentenceStore()
      const entry = this.ensurePaginationEntry(docId, processingId)
      entry.loading = true

      try {
        let pageNumber = 1
        let offset: number | null = null
        let offsets: Array<number | null> = [null]

        while (true) {
          const page = await sentenceStore.fetchSentencesPage(docId, processingId, offset, SENTENCE_ITEM_PER_PAGE)
          const firstSentenceId = page.items[0]?.id ?? null

          if (firstSentenceId === anchorId) {
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
      } finally {
        entry.loading = false
      }
    },

    async initializeDocumentPagination(docId: string, processingId: string): Promise<void> {
      if (!docId || !processingId) {
        return
      }

      this.hydrateFromLocalStorage()
      this.ensurePaginationEntry(docId, processingId)

      const savedAnchor = this.getSentenceAnchor(docId)
      if (savedAnchor) {
        const restored = await this.restorePageByAnchor(docId, processingId, savedAnchor)
        if (restored) {
          return
        }
      }

      await this.loadPage(docId, processingId, null, 1, [null])
    },

    async goToPreviousPage(docId: string, processingId: string): Promise<void> {
      const entry = this.ensurePaginationEntry(docId, processingId)
      if (entry.loading || entry.currentPage <= 1) {
        return
      }

      const previousPageNumber = entry.currentPage - 1
      const previousOffset = entry.offsets[previousPageNumber - 1] ?? null
      await this.loadPage(docId, processingId, previousOffset, previousPageNumber, entry.offsets)
    },

    async goToNextPage(docId: string, processingId: string): Promise<void> {
      const entry = this.ensurePaginationEntry(docId, processingId)
      if (entry.loading || entry.nextAfterStartOffset === null) {
        return
      }

      const nextPageNumber = entry.currentPage + 1
      const nextOffsets = [...entry.offsets.slice(0, entry.currentPage), entry.nextAfterStartOffset]
      await this.loadPage(docId, processingId, entry.nextAfterStartOffset, nextPageNumber, nextOffsets)
    },

    async refreshCurrentPage(docId: string, processingId: string): Promise<void> {
      const entry = this.ensurePaginationEntry(docId, processingId)
      const currentOffset = entry.offsets[entry.currentPage - 1] ?? null
      await this.loadPage(docId, processingId, currentOffset, entry.currentPage, entry.offsets)
    },
  },
})
