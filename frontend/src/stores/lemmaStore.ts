import { defineStore } from 'pinia'

import { post } from '@/stores/fetchWrapper'
import { on } from '@/socket/socket'
import { useProcessStore } from '@/stores/processStore'
import { useSentenceStore } from '@/stores/sentenceStore'
import type { GetLemmaRequest, GetLemmaResponse, LemmaItem, LemmaViewItem } from '@/types/lemmatize'

const PAGE_ITEM_PER_PAGE = Number.parseInt(import.meta.env.VITE_SENTENCE_ITEM_PER_PAGE ?? '10', 10)

function normalizeTokens(tokens: LemmaItem[]): LemmaItem[] {
  return [...tokens].sort((a, b) => a.word_index - b.word_index)
}

function buildSourceText(tokens: LemmaItem[]): string {
  return normalizeTokens(tokens).map((token) => token.source_word).join(' ').trim()
}

function buildLemmaText(tokens: LemmaItem[]): string {
  return normalizeTokens(tokens).map((token) => token.lemma_word).join(' ').trim()
}

export const useLemmaStore = defineStore('lemma-store', {
  state: () => ({
    lemmatize: [] as LemmaItem[],
    connected: false as boolean,
  }),
  getters: {},
  actions: {
    // 1. Socket binding
    bindSocketEvents(): void {
      if (this.connected) {
        return
      }

      on('socket:connected', () => {
        this.connected = true
      })
      on('socket:disconnected', () => {
        this.connected = false
      })
    },

    // 2. API requests
    async getLemmaTokensBySentenceIds(sentenceIds: string[]): Promise<GetLemmaResponse> {
      const normalizedSentenceIds = [...new Set(sentenceIds.filter(Boolean))]
      if (normalizedSentenceIds.length === 0) {
        return {}
      }

      const payload: GetLemmaRequest = { sentence_ids: normalizedSentenceIds }
      const response = await post<GetLemmaResponse>('/api/lemma', payload)
      const tokens = Object.values(response).flat()
      this.upsertLemmaTokens(tokens)
      return response
    },

    // TODO: remove
    async getLemmaItems( segmentationId: string,
      startFromSentenceId: string | null = null,
      limit = PAGE_ITEM_PER_PAGE,
    ): Promise<LemmaViewItem[]> {
      const sentenceStore = useSentenceStore()
      const sentences = sentenceStore.sentences
        .filter((item) => item.version_id === segmentationId)
        .sort((a, b) => a.start_offset - b.start_offset)

      if (sentences.length === 0) {
        return []
      }

      const startIndex = startFromSentenceId
        ? Math.max(0, sentences.findIndex((item) => item.id === startFromSentenceId) + 1)
        : 0
      const targetSentenceIds = sentences
        .slice(startIndex, startIndex + limit)
        .map((item) => item.id)

      if (targetSentenceIds.length === 0) {
        return []
      }

      await this.getLemmaTokensBySentenceIds(targetSentenceIds)
      return this.getLemmaViewsBySentenceIds(targetSentenceIds, segmentationId)
    },

    // 3. Helpers // TODO: remove
    upsertLemmaToken(token: LemmaItem): void {
      const existingIndex = this.lemmatize.findIndex((item) => item.id === token.id)
      if (existingIndex >= 0) {
        this.lemmatize.splice(existingIndex, 1, token)
        return
      }

      this.lemmatize.push(token)
    },

    upsertLemmaTokens(tokens: LemmaItem[]): void {
      for (const token of tokens) {
        this.upsertLemmaToken(token)
      }
    },

    getLemmaTokensBySentenceId(sentenceId: string): LemmaItem[] {
      return this.lemmatize.filter((token) => token.sentence_id === sentenceId)
    },

    getLemmaViewsBySentenceIds(sentenceIds: string[], segmentationId: string): LemmaViewItem[] {
      return sentenceIds.map((sentenceId) => {
        const tokens = this.getLemmaTokensBySentenceId(sentenceId)
        return {
          id: sentenceId,
          segmentation_id: segmentationId,
          sentence_id: sentenceId,
          source_text: buildSourceText(tokens),
          lemma_text: buildLemmaText(tokens),
        }
      })
    },

    getLemmasBySegmentationId(segmentationId: string): LemmaViewItem[] {
      const processStore = useProcessStore()
      const sentenceStore = useSentenceStore()
      const lemmaProcessIds = processStore.processing
        .filter((item) => item.type === 'lemma' && String(item.parent_id) === segmentationId)
        .map((item) => item.id)

      const processIdSet = new Set(lemmaProcessIds)
      const sentenceIds = sentenceStore.sentences
        .filter((item) => item.version_id === segmentationId)
        .sort((a, b) => a.start_offset - b.start_offset)
        .map((item) => item.id)

      return sentenceIds
        .map((sentenceId) => {
          const tokens = this.lemmatize
            .filter((token) => token.sentence_id === sentenceId && processIdSet.has(token.version_id))
          if (tokens.length === 0) {
            return null
          }

          return {
            id: sentenceId,
            segmentation_id: segmentationId,
            sentence_id: sentenceId,
            source_text: buildSourceText(tokens),
            lemma_text: buildLemmaText(tokens),
          }
        })
        .filter((item): item is LemmaViewItem => item !== null)
    },
  },
})
