import { defineStore } from 'pinia'
import { useLemmaStore } from '@/stores/lemmaStore'
import { useSentenceStore } from '@/stores/sentenceStore'

export type PaginationScope = 'sentence' | 'lemma'
export type PaginationAnchorMap = Record<string, string>

type PaginationCursor = string | null

interface PaginationEntry {
  currentPage: number
  offsets: PaginationCursor[]
  hasMore: boolean
  nextCursor: PaginationCursor
  loading: boolean
  processingId: string
  pageItemIds: string[]
}

interface LoadedPage {
  itemIds: string[]
  firstItemId: string | null
  hasMore: boolean
  nextCursor: PaginationCursor
}

const PAGE_ITEM_PER_PAGE = Number.parseInt(import.meta.env.VITE_SENTENCE_ITEM_PER_PAGE ?? '10', 10)
const PAGINATION_ANCHOR_STORAGE_KEY = 'corpustar.pagination-anchors'

function createEntry(processingId = ''): PaginationEntry {
  return {
    currentPage: 1,
    offsets: [null],
    hasMore: false,
    nextCursor: null,
    loading: false,
    processingId,
    pageItemIds: [],
  }
}

function getAnchorKey(docId: string, scope: PaginationScope): string {
  return `${scope}::${docId}`
}

function getEntryKey(docId: string, scope: PaginationScope): string {
  return `${scope}::${docId}`
}

function readPaginationAnchors(): PaginationAnchorMap {
  if (typeof window === 'undefined') {
    return {}
  }

  try {
    return JSON.parse(window.localStorage.getItem(PAGINATION_ANCHOR_STORAGE_KEY) ?? '{}') as PaginationAnchorMap
  } catch {
    return {}
  }
}

export const usePaginationStore = defineStore('pagination-store', {
  state: () => ({
    paginationAnchors: {} as PaginationAnchorMap,
    paginationByScopeKey: {} as Record<string, PaginationEntry>,
    hydrated: false,
  }),
  getters: {
    getPaginationAnchor: (state) => (docId: string, scope: PaginationScope = 'sentence'): string | null => (
      state.paginationAnchors[getAnchorKey(docId, scope)]
      ?? (scope === 'sentence' ? state.paginationAnchors[docId] ?? null : null)
    ),
    getPaginationEntry: (state) => (
      docId: string,
      scope: PaginationScope = 'sentence',
    ): PaginationEntry => state.paginationByScopeKey[getEntryKey(docId, scope)] ?? createEntry(),
  },
  actions: {
    hydrateFromLocalStorage(): void {
      if (this.hydrated) {
        return
      }

      this.paginationAnchors = readPaginationAnchors()
      this.hydrated = true
    },

    persist(): void {
      if (typeof window === 'undefined') {
        return
      }

      window.localStorage.setItem(PAGINATION_ANCHOR_STORAGE_KEY, JSON.stringify(this.paginationAnchors))
    },

    entry(docId: string, scope: PaginationScope, processingId = ''): PaginationEntry {
      const entryKey = getEntryKey(docId, scope)
      const current = this.paginationByScopeKey[entryKey]
      if (!current || (processingId && current.processingId !== processingId)) {
        const next = createEntry(processingId)
        this.paginationByScopeKey[entryKey] = next
        return next
      }

      return current
    },

    saveAnchor(docId: string, scope: PaginationScope, itemId: string | null): void {
      const anchorKey = getAnchorKey(docId, scope)
      if (!itemId) {
        delete this.paginationAnchors[anchorKey]
        if (scope === 'sentence') {
          delete this.paginationAnchors[docId]
        }
      } else {
        this.paginationAnchors[anchorKey] = itemId
      }

      this.persist()
    },

    async fetchPage(
      docId: string,
      processingId: string,
      scope: PaginationScope,
      cursor: PaginationCursor,
      syncSentenceStore = true,
    ): Promise<LoadedPage> {
      if (scope === 'sentence') {
        const sentenceStore = useSentenceStore()
        const page = await sentenceStore.getSentences(
          docId,
          processingId,
          cursor,
          PAGE_ITEM_PER_PAGE,
          syncSentenceStore,
        )

        return {
          itemIds: page.sentences.map((item) => item.id),
          firstItemId: page.sentences[0]?.id ?? null,
          hasMore: page.cursor.nextCursor !== null,
          nextCursor: page.cursor.nextCursor,
        }
      }

      const lemmaStore = useLemmaStore()
      const fetchedItems = await lemmaStore.getLemmaItems(
        processingId,
        cursor,
        PAGE_ITEM_PER_PAGE + 1,
      )
      const pageItems = fetchedItems.slice(0, PAGE_ITEM_PER_PAGE)
      const visibleItems = (
        pageItems.length > 0 || cursor !== null
          ? pageItems
          : lemmaStore.getLemmasBySegmentationId(processingId).slice(0, PAGE_ITEM_PER_PAGE)
      )

      return {
        itemIds: visibleItems.map((item) => item.id),
        firstItemId: visibleItems[0]?.id ?? null,
        hasMore: fetchedItems.length > PAGE_ITEM_PER_PAGE,
        nextCursor: visibleItems[visibleItems.length - 1]?.id ?? null,
      }
    },

    async loadPage(
      docId: string,
      processingId: string,
      scope: PaginationScope,
      cursor: PaginationCursor,
      pageNumber: number,
      offsets: PaginationCursor[],
    ): Promise<void> {
      const entry = this.entry(docId, scope, processingId)
      entry.loading = true

      try {
        const page = await this.fetchPage(docId, processingId, scope, cursor)
        entry.currentPage = pageNumber
        entry.offsets = offsets
        entry.hasMore = page.hasMore
        entry.nextCursor = page.nextCursor
        entry.processingId = processingId
        entry.pageItemIds = page.itemIds
        this.saveAnchor(docId, scope, page.firstItemId)
      } finally {
        entry.loading = false
      }
    },

    async restoreSavedPage(
      docId: string,
      processingId: string,
      scope: PaginationScope,
      anchorId: string,
    ): Promise<boolean> {
      let cursor: PaginationCursor = null
      let pageNumber = 1
      let offsets: PaginationCursor[] = [null]

      while (true) {
        const page = await this.fetchPage(docId, processingId, scope, cursor, false)
        if (page.firstItemId === anchorId) {
          await this.loadPage(docId, processingId, scope, cursor, pageNumber, offsets)
          return true
        }

        if (!page.hasMore || page.nextCursor === null) {
          return false
        }

        cursor = page.nextCursor
        pageNumber += 1
        offsets = [...offsets, cursor]
      }
    },

    async initializeDocumentPagination(
      docId: string,
      processingId: string,
      scope: PaginationScope = 'sentence',
    ): Promise<void> {
      this.hydrateFromLocalStorage()
      this.entry(docId, scope, processingId)

      const savedAnchor = this.getPaginationAnchor(docId, scope)
      if (savedAnchor && await this.restoreSavedPage(docId, processingId, scope, savedAnchor)) {
        return
      }

      await this.loadPage(docId, processingId, scope, null, 1, [null])
    },

    async goToPreviousPage(
      docId: string,
      processingId: string,
      scope: PaginationScope = 'sentence',
    ): Promise<void> {
      const entry = this.entry(docId, scope, processingId)
      if (entry.loading || entry.currentPage <= 1) {
        return
      }

      const previousPage = entry.currentPage - 1
      await this.loadPage(
        docId,
        processingId,
        scope,
        entry.offsets[previousPage - 1] ?? null,
        previousPage,
        entry.offsets,
      )
    },

    async goToNextPage(
      docId: string,
      processingId: string,
      scope: PaginationScope = 'sentence',
    ): Promise<void> {
      const entry = this.entry(docId, scope, processingId)
      if (entry.loading || !entry.hasMore || entry.nextCursor === null) {
        return
      }

      const nextPage = entry.currentPage + 1
      const nextOffsets = [...entry.offsets.slice(0, entry.currentPage), entry.nextCursor]
      await this.loadPage(docId, processingId, scope, entry.nextCursor, nextPage, nextOffsets)
    },

    async refreshCurrentPage(
      docId: string,
      processingId: string,
      scope: PaginationScope = 'sentence',
    ): Promise<void> {
      const entry = this.entry(docId, scope, processingId)
      await this.loadPage(
        docId,
        processingId,
        scope,
        entry.offsets[entry.currentPage - 1] ?? null,
        entry.currentPage,
        entry.offsets,
      )
    },
  },
})
