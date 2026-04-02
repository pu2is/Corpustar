import { defineStore } from 'pinia'

export interface CursorItem {
  currentCursor: string | null
  prevCursor: string | null
  nextCursor: string | null
  page: number
}

export interface PagenationInfoItem {
  sentenceTable: Record<string, CursorItem>
}

export const usePaginationStore = defineStore('pagination-store', {
  state: () => ({
    paginationInfo: {
      sentenceTable: {},
    } as PagenationInfoItem,
  }),
  actions: {
    loadPagination(): void {
      this.paginationInfo = JSON.parse(
        localStorage.getItem('paginationInfo') ?? '{"sentenceTable":{}}',
      ) as PagenationInfoItem
    },
    savePagination(payload: { section: 'sentenceTable', cursor: Record<string, CursorItem> }): void {
      this.paginationInfo[payload.section] = payload.cursor
      localStorage.setItem('paginationInfo', JSON.stringify(this.paginationInfo))
    },
  },
})
