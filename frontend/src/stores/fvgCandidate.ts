import { defineStore } from 'pinia'

import { post } from '@/stores/fetchWrapper'
// types
import type {
  FvgCandidateListRequest,
  FvgCandidateFilteredListRequest,
  FvgCursorItem,
  SentenceFvgItem,
} from '@/types/fvg'

const DEFAULT_LIMIT = Number.parseInt(import.meta.env.VITE_SENTENCE_ITEM_PER_PAGE ?? '10', 10)

export const useFvgCandidateStore = defineStore('fvg-candidate-store', {
  state: () => ({
    sentenceFvgList: [] as SentenceFvgItem[],
    cursor: null as FvgCursorItem | null,
    display: 'detected' as 'detected' | 'undetected' | 'all',
    connected: false as boolean,
  }),
  actions: {
    async getFvgCandidates(segmentationId: string, cursor: string | null = null, limit: number = DEFAULT_LIMIT): Promise<void> {
      const payload: FvgCandidateListRequest = { segmentation_id: segmentationId, cursor, limit }
      const response = await post<{ sentences: SentenceFvgItem[]; cursor: FvgCursorItem }>('/api/fvg_candidates', payload)
      this.sentenceFvgList = response.sentences
      this.cursor = response.cursor
    },

    async getDetectedFvgCandidates(fvgProcessId: string, cursor: string | null = null, limit: number = DEFAULT_LIMIT): Promise<void> {
      const payload: FvgCandidateFilteredListRequest = { fvg_process_id: fvgProcessId, cursor, limit }
      const response = await post<{ sentences: SentenceFvgItem[]; cursor: FvgCursorItem }>('/api/fvg_candidates/detected', payload)
      this.sentenceFvgList = response.sentences
      this.cursor = response.cursor
    },

    async getUndetectedFvgCandidates(fvgProcessId: string, cursor: string | null = null, limit: number = DEFAULT_LIMIT): Promise<void> {
      const payload: FvgCandidateFilteredListRequest = { fvg_process_id: fvgProcessId, cursor, limit }
      const response = await post<{ sentences: SentenceFvgItem[]; cursor: FvgCursorItem }>('/api/fvg_candidates/undetected', payload)
      this.sentenceFvgList = response.sentences
      this.cursor = response.cursor
    },

    // helper
    changeDisplay(display: 'detected' | 'undetected' | 'all'): void {
      this.display = display
    },
  },
})
