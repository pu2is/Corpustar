import { defineStore } from 'pinia'
import { get, post } from '@/stores/fetchWrapper'
import { on, SOCKET_CONNECTED_EVENT, SOCKET_DISCONNECTED_EVENT } from '@/socket/socket'
import type { ActionResponse } from '@/types/lemmas'
import type { ProcessingItem, ProcessingState, ProcessingType } from '@/types/processings'
import type { SentenceSegmentationResponse } from '@/types/sentences'

type ProcessItem = ProcessingItem

const PROCESSING_STATE_SET = new Set<ProcessingState>(['running', 'succeed', 'failed'])
const sentenceItemPerPage = Number.parseInt(import.meta.env.VITE_SENTENCE_ITEM_PER_PAGE ?? '10')

export const useProcessStore = defineStore('process-store', {
  state: () => ({
    processes: [] as ProcessItem[],
    connected: false,
  }),
  getters: {
    getProcessesByDocId: (state) => (docId: string): ProcessItem[] => {
      if (!docId) {
        return []
      }

      return state.processes.filter((process) => process.docId === docId)
    },
    getSentenceSegmentationProcessByDocId: (state) => (docId: string): ProcessItem | null => {
      if (!docId) {
        return null
      }

      return state.processes.find((process) => (
        process.docId === docId
        && process.type === 'sentence_segmentation'
        && process.state === 'succeed'
      )) ?? null
    },
    getLemmatizeProcessBySegmentationId: (state) => (docId: string, segmentationId: string): ProcessItem | null => {
      if (!docId || !segmentationId) {
        return null
      }

      return state.processes.find((process) => (
        process.docId === docId
        && process.type === 'lemmatize'
        && process.meta?.segmentationId === segmentationId
      )) ?? null
    },
    getSegmentationStateByDocId: (state) => (docId: string): ProcessingState | null => {
      if (!docId) { return null }

      return state.processes.find((process) => (
        process.docId === docId && process.type === 'sentence_segmentation'
      ))?.state ?? null
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

    toProcessingState(value: unknown): ProcessingState | null {
      const normalized = this.toNonEmptyString(value)
      if (!normalized || !PROCESSING_STATE_SET.has(normalized as ProcessingState)) {
        return null
      }

      return normalized as ProcessingState
    },

    toProcessingItem(payload: unknown): ProcessItem | null {
      if (!this.isRecord(payload)) {
        return null
      }

      const id = this.toNonEmptyString(payload.id)
      const docId = this.toNonEmptyString(payload.docId)
      const type = this.toNonEmptyString(payload.type) as ProcessingType | null
      const state = this.toProcessingState(payload.state)
      const createdAt = this.toNonEmptyString(payload.createdAt)
      const updatedAt = this.toNonEmptyString(payload.updatedAt)
      const errorMessage = payload.errorMessage === null
        ? null
        : (this.toNonEmptyString(payload.errorMessage) ?? null)

      if (!id || !docId || !type || !state || !createdAt || !updatedAt) {
        return null
      }

      return {
        id,
        docId,
        type,
        state,
        createdAt,
        updatedAt,
        errorMessage,
        meta: this.isRecord(payload.meta) ? payload.meta : null,
      }
    },

    bindSocketEvents(): void {
      on(SOCKET_CONNECTED_EVENT, () => {
        this.connected = true
        void this.getAllProcesses().catch(() => undefined)
      })
      on(SOCKET_DISCONNECTED_EVENT, () => {
        this.connected = false
        this.processes = []
      })
      on('process:created', (payload) => {
        this.handleProcessingCreated(payload)
      })
      on('process:updated', (payload) => {
        this.handleProcessingUpdated(payload)
      })
    },

    findProcessById(processingId: string): ProcessItem | undefined {
      return this.processes.find((process) => process.id === processingId)
    },

    // Get
    async getAllProcesses(): Promise<ProcessItem[]> {
      const processes = await get<ProcessItem[]>('/api/processes')
      this.processes = processes
      return processes
    },

    // Post: segment sentence
    async segmentDocument(docId: string): Promise<SentenceSegmentationResponse> {
      const response = await post<SentenceSegmentationResponse>(
        `/api/process/sentence_segmentation/${encodeURIComponent(docId)}`,
        undefined,
        {params: {preview_length: sentenceItemPerPage},
        },
      )
      this.upsertProcess(response.processing)
      return response
    },

    async lemmatizeSegmentation(docId: string, segmentationId: string): Promise<ActionResponse> {
      return post<ActionResponse>(
        `/api/process/lemmatize/${encodeURIComponent(segmentationId)}`,
        {
          doc_id: docId,
          segmentation_id: segmentationId,
          preview_length: sentenceItemPerPage,
        },
      )
    },

    // Socket event handlers
    handleProcessingCreated(payload: unknown): void {
      const processing = this.toProcessingItem(payload)
      if (!processing) {
        return
      }

      this.upsertProcess(processing)
    },

    handleProcessingUpdated(payload: unknown): void {
      const processing = this.toProcessingItem(payload)
      if (!processing) {
        return
      }

      this.upsertProcess(processing)
    },

    // helper
    upsertProcess(processing: ProcessItem): void {
      const existingIndex = this.processes.findIndex((existing) => existing.id === processing.id)
      if (existingIndex >= 0) {
        this.processes.splice(existingIndex, 1, processing)
        return
      }

      this.processes.unshift(processing)
    },
  },
})
