import { defineStore } from 'pinia'
import { get, post } from '@/stores/fetchWrapper'
import { on, SOCKET_CONNECTED_EVENT, SOCKET_DISCONNECTED_EVENT } from '@/socket/socket'
import type { ProcessingItem, ProcessingState, ProcessingType } from '@/types/processings'
import type { SentenceSegmentationResponse } from '@/types/sentences'

type ProcessItem = ProcessingItem

const PROCESSING_STATE_SET = new Set<ProcessingState>(['running', 'succeed', 'failed'])
const sentenceItemPerPage = Number.parseInt(import.meta.env.VITE_SENTENCE_ITEM_PER_PAGE ?? '20', 10)

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function toNonEmptyString(value: unknown): string | null {
  if (typeof value !== 'string') {
    return null
  }

  const trimmed = value.trim()
  return trimmed.length ? trimmed : null
}

function toProcessingState(value: unknown): ProcessingState | undefined {
  const normalized = toNonEmptyString(value)
  if (!normalized || !PROCESSING_STATE_SET.has(normalized as ProcessingState)) {
    return undefined
  }
  return normalized as ProcessingState
}

function toProcessingItem(payload: unknown): ProcessItem | null {
  if (!isRecord(payload)) {
    return null
  }

  const id = toNonEmptyString(payload.id)
  const docId = toNonEmptyString(payload.docId)
  const type = toNonEmptyString(payload.type) as ProcessingType | null
  const state = toProcessingState(payload.state)
  const createdAt = toNonEmptyString(payload.createdAt)
  const updatedAt = toNonEmptyString(payload.updatedAt)
  const errorMessage = payload.errorMessage === null
    ? null
    : (toNonEmptyString(payload.errorMessage) ?? null)
  const meta = isRecord(payload.meta) ? payload.meta : null

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
    meta,
  }
}

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
    getSegmentationStateByDocId: (state) => (docId: string): ProcessingState | null => {
      if (!docId) { return null }

      return state.processes.find((process) => (
        process.docId === docId && process.type === 'sentence_segmentation'
      ))?.state ?? null
    },
  },
  actions: {
    bindSocketEvents(): void {
      on(SOCKET_CONNECTED_EVENT, () => {
        this.connected = true
        void this.getAllProcesses().catch(() => undefined)
      })
      on(SOCKET_DISCONNECTED_EVENT, () => {
        this.connected = false
      })
      on('processing:created', (payload) => {
        this.handleProcessingCreated(payload)
      })
      on('processing:updated', (payload) => {
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

    // Socket event handlers
    handleProcessingCreated(payload: unknown): void {
      const processing = toProcessingItem(payload)
      if (!processing) {
        return
      }

      this.upsertProcess(processing)
    },

    handleProcessingUpdated(payload: unknown): void {
      const processing = toProcessingItem(payload)
      if (!processing) {
        return
      }

      const existingIndex = this.processes.findIndex((existing) => existing.id === processing.id)
      if (existingIndex >= 0) {
        this.processes.splice(existingIndex, 1, processing)
      }
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
