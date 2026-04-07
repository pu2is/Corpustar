import { defineStore } from 'pinia'

import { post, get } from '@/stores/fetchWrapper'
import { on } from '@/socket/socket'
import { SOCKET_EVENT } from '@/socket/events'
// types
import type {
  FvgCandidateItem,
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
    simpleStatistics: null as { num_verb: number; num_aux: number; num_fvg: number; num_sentences: number } | null,
  }),
  actions: {
    
    bindSocketEvents(): void {
      if (this.connected) return
      on(SOCKET_EVENT.FVG_CANDIDATE_REMOVE_FAILED, (_socketMsg) => { /* no-op */ })
      on(SOCKET_EVENT.FVG_CANDIDATE_RESTORE_FAILED, (_socketMsg) => { /* no-op */ })
      on(SOCKET_EVENT.FVG_CANDIDATE_ADD_SUCCEED, (_socketMsg) => { /* no-op */ })
      on(SOCKET_EVENT.FVG_CANDIDATE_ADD_FAILED, (_socketMsg) => { /* no-op */ })
      on(SOCKET_EVENT.FVG_RESULTS_REMOVED, (socketMsg) => {
        const payload = socketMsg as { fvg_process_id: string; lemma_process_id: string }
        const isAffected = this.sentenceFvgList.some((s) =>
          s.lemma_tokens?.some((t) => String(t.version_id) === payload.lemma_process_id),
        )
        if (isAffected) {
          this.sentenceFvgList = []
          this.cursor = null
        }
      })
      this.connected = true
    },

    async getSentences(segmentationId: string, cursor: string | null = null, limit: number = DEFAULT_LIMIT): Promise<void> {
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

    toggleCandidateRemoved(candidateId: string): void {
      const candidate = this.sentenceFvgList
        .flatMap((s) => s.fvg_candidates)
        .find((c) => c.id === candidateId)
      if (candidate) candidate.removed = !candidate.removed
    },

    async removeFvgCandidate(sentenceId: string, fvgCandidateId: string): Promise<void> {
      const response = await post<{ sentence_id: string; fvg_candidate: FvgCandidateItem }>(
        '/api/fvg_candidates/remove',
        { sentence_id: sentenceId, fvg_candidate_id: fvgCandidateId },
      )
      const sentence = this.sentenceFvgList.find((s) => s.id === response.sentence_id)
      if (!sentence) return
      const idx = sentence.fvg_candidates.findIndex((c) => c.id === response.fvg_candidate.id)
      if (idx !== -1) sentence.fvg_candidates[idx] = response.fvg_candidate
    },

    async restoreFvgCandidate(sentenceId: string, fvgCandidateId: string): Promise<void> {
      const response = await post<{ sentence_id: string; fvg_candidate: FvgCandidateItem }>(
        '/api/fvg_candidates/restore',
        { sentence_id: sentenceId, fvg_candidate_id: fvgCandidateId },
      )
      const sentence = this.sentenceFvgList.find((s) => s.id === response.sentence_id)
      if (!sentence) return
      const idx = sentence.fvg_candidates.findIndex((c) => c.id === response.fvg_candidate.id)
      if (idx !== -1) sentence.fvg_candidates[idx] = response.fvg_candidate
    },

    async addFvgCandidate(
      sentenceId: string,
      processId: string,
      fvgEntryId: string,
      verbId: string,
      nounId: string,
      prepId: string = '',
    ): Promise<void> {
      const response = await post<{ sentence_id: string; fvg_candidate: FvgCandidateItem } | null>(
        '/api/fvg_candidates/add',
        { sentence_id: sentenceId, process_id: processId, fvg_entry_id: fvgEntryId, verb_id: verbId, noun_id: nounId, prep_id: prepId },
      )
      if (!response) return
      const sentence = this.sentenceFvgList.find((s) => s.id === response.sentence_id)
      if (!sentence) return
      sentence.fvg_candidates.push(response.fvg_candidate)
    },

    // helper
    changeDisplay(display: 'detected' | 'undetected' | 'all'): void {
      this.display = display
    },

    async getSimpleStatistics(fvgProcessId: string): Promise<void> {
      const response = await get<{ num_verb: number; num_aux: number; num_fvg: number; num_sentences: number }>(
        `/api/fvg_candidates/statistics/${fvgProcessId}`,
      )
      this.simpleStatistics = response
    },

    resetStatistics(): void {
      this.simpleStatistics = null
    },
  },
})
