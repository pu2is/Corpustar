import { defineStore } from 'pinia'

export interface CursorItem {
  currentCursor: string | null
  nextCursor: string | null
  page: number
}

export type FvgSentenceTableMode = 'all' | 'matched' | 'unmatched'

export interface PagenationInfoItem {
  sentenceTable: Record<string, CursorItem>
  fvgSentenceTable: Partial<Record<FvgSentenceTableMode, CursorItem>>
}

export const usePaginationStore = defineStore('pagination-store', {
  state: () => ({
    paginationInfo: {
      sentenceTable: {},
      fvgSentenceTable: {},
    } as PagenationInfoItem,
  }),
  actions: {
    loadPagination(): void {
      const stored = JSON.parse(
        localStorage.getItem('paginationInfo') ?? '{}',
      ) as Partial<PagenationInfoItem>
      this.paginationInfo = {
        sentenceTable: stored.sentenceTable ?? {},
        fvgSentenceTable: stored.fvgSentenceTable ?? {},
      }
    },
    savePagination(payload:
      | { section: 'sentenceTable'; cursor: Record<string, CursorItem> }
      | { section: 'fvgSentenceTable'; cursor: Partial<Record<FvgSentenceTableMode, CursorItem>> }
    ): void {
      if (payload.section === 'sentenceTable') {
        this.paginationInfo.sentenceTable = payload.cursor
      } else {
        this.paginationInfo.fvgSentenceTable = payload.cursor
      }
      localStorage.setItem('paginationInfo', JSON.stringify(this.paginationInfo))
    },
  },
})
