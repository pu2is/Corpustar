import { defineStore } from 'pinia'
import { get, post } from '@/stores/fetchWrapper'
import { on, SOCKET_CONNECTED_EVENT, SOCKET_DISCONNECTED_EVENT } from '@/socket/socket'
import type { ActionResponse, LemmaItem } from '@/types/lemmas'

export const useLemmaStore = defineStore('lemma-store', {
  state: () => ({
    lemmas: [] as LemmaItem[],
    connected: false,
  }),
  getters: {
    getLemmasBySegmentationId: (state) => (segmentationId: string): LemmaItem[] => {
      if (!segmentationId) {
        return []
      }

      return state.lemmas.filter((lemma) => lemma.segmentationId === segmentationId)
    },
  },
  actions: {
    isRecord(value: unknown): value is Record<string, unknown> {
      return typeof value === 'object' && value !== null
    },

    toNonEmptyString(value: unknown): string | null {
      if (typeof value !== 'string') {
        return null
      }

      const trimmed = value.trim()
      return trimmed.length ? trimmed : null
    },

    toLemmaItem(payload: unknown): LemmaItem | null {
      if (!this.isRecord(payload)) {
        return null
      }

      const id = this.toNonEmptyString(payload.id)
      const docId = this.toNonEmptyString(payload.docId)
      const segmentationId = this.toNonEmptyString(payload.segmentationId)
      const sentenceId = this.toNonEmptyString(payload.sentenceId)
      const sourceText = typeof payload.sourceText === 'string' ? payload.sourceText : null
      const lemmaText = typeof payload.lemmaText === 'string' ? payload.lemmaText : null
      const correctedLemma = typeof payload.correctedLemma === 'string' ? payload.correctedLemma : null
      const fvgResultId = payload.fvgResultId === null
        ? null
        : (this.toNonEmptyString(payload.fvgResultId) ?? null)

      if (!id || !docId || !segmentationId || !sentenceId || sourceText === null || !lemmaText || correctedLemma === null) {
        return null
      }

      return {
        id,
        docId,
        segmentationId,
        sentenceId,
        sourceText,
        lemmaText,
        correctedLemma,
        fvgResultId,
      }
    },

    toLemmaItems(payload: unknown): LemmaItem[] {
      if (!Array.isArray(payload)) {
        return []
      }

      return payload
        .map((item) => this.toLemmaItem(item))
        .filter((item): item is LemmaItem => item !== null)
    },

    bindSocketEvents(): void {
      on(SOCKET_CONNECTED_EVENT, () => {
        this.connected = true
      })
      on(SOCKET_DISCONNECTED_EVENT, () => {
        this.connected = false
      })
      on('lemma:created', (payload) => {
        this.upsertLemmas(this.toLemmaItems(payload))
      })
      on('lemma:updated', (payload) => {
        const lemma = this.toLemmaItem(payload)
        if (!lemma) {
          return
        }

        this.upsertLemma(lemma)
      })
    },

    async editLemmaItem(id: string, newLemma: string): Promise<ActionResponse> {
      return post<ActionResponse>(`/api/lemma/correct/${encodeURIComponent(id)}`, {
        id,
        corrected_lemma: newLemma,
      })
    },

    async getLemmaItems(
      segmentationId: string,
      startFromId: string | null = null,
      limit = Number.parseInt(import.meta.env.VITE_SENTENCE_ITEM_PER_PAGE ?? '10', 10),
    ): Promise<LemmaItem[]> {
      const items = await get<LemmaItem[]>(`/api/lemma/${encodeURIComponent(segmentationId)}`, {
        params: {
          start_lemma_id: startFromId,
          limit,
        },
      })
      this.upsertLemmas(items)
      return items
    },

    upsertLemma(lemma: LemmaItem): void {
      const existingIndex = this.lemmas.findIndex((existing) => existing.id === lemma.id)
      if (existingIndex >= 0) {
        this.lemmas.splice(existingIndex, 1, lemma)
        return
      }

      this.lemmas.push(lemma)
    },

    upsertLemmas(lemmas: LemmaItem[]): void {
      for (const lemma of lemmas) {
        this.upsertLemma(lemma)
      }
    },
  },
})
