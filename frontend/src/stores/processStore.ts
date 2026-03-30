import { defineStore } from 'pinia'

import { get, post } from '@/stores/fetchWrapper'
import { on } from '@/socket/socket'
// types
import type { ProcessResponse, ProcessResponseWithId } from '@/types/general'
import type { ImportRuleProcessRequest, LemmatizeRequest, ProcessingItem, SentenceSegmentationRequest} from '@/types/processings'

const PREVIEW_LENGTH = Number.parseInt(import.meta.env.VITE_SENTENCE_ITEM_PER_PAGE ?? '10', 10)

export const useProcessStore = defineStore('process-store', {
  state: () => ({
    processing: [] as ProcessingItem[],
    connected: false as boolean,
    running: false as boolean,
  }),
  getters: {
    getProcessByDocId: (state) => (docId: string): ProcessingItem[] => (
      state.processing.filter((item) => item.doc_id === docId)
    ),
    getProcessById: (state) => (processId: string): ProcessingItem | undefined => (
      state.processing.find((item) => item.id === processId)
    ),
    getSentenceSegmentationProcessByDocId: (state) => (docId: string): ProcessingItem | null => (
      state.processing.find((item) => (
        item.doc_id === docId
        && item.type === 'sentence_segmentation'
        && item.state === 'succeed'
      )) ?? null
    ),
    getLemmatizeProcessBySegmentationId: (state) => (docId: string, segmentationId: string): ProcessingItem | null => (
      state.processing.find((item) => (
        item.doc_id === docId
        && item.type === 'lemma'
        && String(item.meta?.segmentation_id ?? '') === segmentationId
      )) ?? null
    ),
  },
  actions: {
    // 1. Socket binding
    bindSocketEvents(): void {
      if (this.connected) {
        return
      }
      on('socket:connected', async () => {
        this.connected = true
        this.processing = await this.getAllProcesses()
      })
      on('socket:disconnected', () => {
        this.connected = false
        this.processing = []
      })
      on('importRule:started', (socketMsg) => {
        const payload = socketMsg as ProcessingItem
        this.processing.unshift(payload)
        this.running = true
      })
      on('importRule:succeed', (socketMsg) => {
        const payload = socketMsg as { processing?: ProcessingItem }
        const processItem = payload.processing
        if (!processItem) {
          this.running = false
          return
        }

        const targetIndex = this.processing.findIndex((item) => item.id === processItem.id)
        if (targetIndex >= 0) {
          this.processing.splice(targetIndex, 1, processItem)
        } else {
          this.processing.unshift(processItem)
        }
        this.running = false
      })
      on('segmentation:started', (socketMsg) => {
        const payload = socketMsg as ProcessingItem
        this.processing.unshift(payload)
        this.running = true
      })
      on('segmentation:succeed', (socketMsg) => {
        const payload = socketMsg as { processing?: ProcessingItem }
        const processItem = payload.processing
        if (!processItem) {
          this.running = false
          return
        }

        const targetIndex = this.processing.findIndex((item) => item.id === processItem.id)
        if (targetIndex >= 0) {
          this.processing.splice(targetIndex, 1, processItem)
        } else {
          this.processing.unshift(processItem)
        }
        this.running = false
      })
      on('lemmatize:started', (socketMsg) => {
        const payload = socketMsg as ProcessingItem
        this.processing.unshift(payload)
        this.running = true
      })
      on('lemmatize:succeed', (socketMsg) => {
        const payload = socketMsg as ProcessingItem
        const targetIndex = this.processing.findIndex((item) => item.id === payload.id)
        if (targetIndex >= 0) {
          this.processing.splice(targetIndex, 1, payload)
        } else {
          this.processing.unshift(payload)
        }
        this.running = false
      })
    },

    // 2. API requests
    async getAllProcesses(): Promise<ProcessingItem[]> {
      const items = await get<ProcessingItem[]>('/api/process')
      this.processing = items
      this.running = items.some((item) => item.state === 'running')
      return items
    },

    async importRule(payload: ImportRuleProcessRequest): Promise<ProcessResponse> {
      return post<ProcessResponse>('/api/process/import_rule', payload)
    },

    async segmentDocument(docId: string): Promise<ProcessResponseWithId> {
      const payload: SentenceSegmentationRequest = {
        doc_id: docId,
        preview_length: PREVIEW_LENGTH,
      }
      return post<ProcessResponseWithId>('/api/process/sentence_segmentation', payload)
    },

    async lemmatizeSegmentation(_docId: string, segmentationId: string): Promise<ProcessResponseWithId> {
      const payload: LemmatizeRequest = { segmentation_id: segmentationId }
      return post<ProcessResponseWithId>('/api/process/lemmatize', payload)
    },

    // 3. Helpers
    upsertProcessing(item: ProcessingItem): void {
      const existingIndex = this.processing.findIndex((entry) => entry.id === item.id)
      if (existingIndex >= 0) {
        this.processing.splice(existingIndex, 1, item)
        return
      }

      this.processing.unshift(item)
    },
  },
})
