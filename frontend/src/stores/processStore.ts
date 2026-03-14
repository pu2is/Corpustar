import { defineStore } from 'pinia'
import { get, post } from '@/stores/fetchWrapper'
import { on } from '@/socket/socket'
import type { ProcessingItem, ProcessingState, ProcessingType } from '@/types/processings'
import type { SentenceSegmentationResponse } from '@/types/sentences'

type ProcessItem = ProcessingItem

interface ProcessState {
  processes: ProcessItem[]
  loading: boolean
  error: string | null
  socketBound: boolean
  socketUnsubscribers: Array<() => void>
}

interface ProcessingEventPayload {
  docId: string
  processingId: string
  state?: ProcessingState
  errorMessage?: string | null
}

interface SentenceListRebuiltPayload {
  docId: string
  processingId: string
}

const PROCESSING_STATE_SET = new Set<ProcessingState>(['running', 'succeed', 'failed'])

function toErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

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

function parseProcessingEventPayload(payload: unknown): ProcessingEventPayload | null {
  if (!isRecord(payload)) {
    return null
  }

  const docId = toNonEmptyString(payload.docId)
  const processingId = toNonEmptyString(payload.processingId)
  if (!docId || !processingId) {
    return null
  }

  const state = toProcessingState(payload.state)
  const errorMessage = payload.errorMessage === null
    ? null
    : (toNonEmptyString(payload.errorMessage) ?? undefined)

  return {
    docId,
    processingId,
    state,
    errorMessage,
  }
}

function parseSentenceListRebuiltPayload(payload: unknown): SentenceListRebuiltPayload | null {
  if (!isRecord(payload)) {
    return null
  }

  const docId = toNonEmptyString(payload.docId)
  const processingId = toNonEmptyString(payload.processingId)
  if (!docId || !processingId) {
    return null
  }

  return {
    docId,
    processingId,
  }
}

function buildProcessingFromEvent(
  existing: ProcessItem | undefined,
  payload: ProcessingEventPayload,
  options?: {
    fallbackState?: ProcessingState
  },
): ProcessItem {
  const nowIso = new Date().toISOString()
  const fallbackState: ProcessingState = options?.fallbackState
    ?? existing?.state
    ?? 'running'
  const type: ProcessingType = existing?.type ?? 'sentence_segmentation'

  return {
    id: payload.processingId,
    docId: payload.docId,
    type,
    state: payload.state ?? fallbackState,
    createdAt: existing?.createdAt ?? nowIso,
    updatedAt: nowIso,
    errorMessage: payload.errorMessage !== undefined
      ? payload.errorMessage
      : (existing?.errorMessage ?? null),
    meta: existing?.meta ?? null,
  }
}

export const useProcessStore = defineStore('process-store', {
  state: (): ProcessState => ({
    processes: [],
    loading: false,
    error: null,
    socketBound: false,
    socketUnsubscribers: [],
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
      )) ?? null
    },
  },
  actions: {
    bindSocketEvents(): void {
      if (this.socketBound) {
        return
      }

      const unbindOnConnected = on('socket:connected', () => {
        void this.getAllProcesses().catch(() => undefined)
      })
      const unbindOnCreated = on('processing:created', (payload) => {
        this.handleProcessingCreated(payload)
      })
      const unbindOnUpdated = on('processing:updated', (payload) => {
        this.handleProcessingUpdated(payload)
      })
      const unbindOnListRebuilt = on('sentence:list_rebuilt', (payload) => {
        this.handleSentenceListRebuilt(payload)
      })

      this.socketUnsubscribers = [
        unbindOnConnected,
        unbindOnCreated,
        unbindOnUpdated,
        unbindOnListRebuilt,
      ]
      this.socketBound = true
    },

    unbindSocketEvents(): void {
      for (const unsubscribe of this.socketUnsubscribers) {
        unsubscribe()
      }

      this.socketUnsubscribers = []
      this.socketBound = false
    },

    findProcessById(processingId: string): ProcessItem | undefined {
      return this.processes.find((process) => process.id === processingId)
    },

    upsertProcess(processing: ProcessItem): void {
      const existingIndex = this.processes.findIndex((existing) => existing.id === processing.id)
      if (existingIndex >= 0) {
        this.processes.splice(existingIndex, 1, processing)
        return
      }

      this.processes.unshift(processing)
    },

    handleProcessingCreated(payload: unknown): void {
      const parsed = parseProcessingEventPayload(payload)
      if (!parsed) {
        return
      }

      const existing = this.findProcessById(parsed.processingId)
      const processing = buildProcessingFromEvent(existing, parsed, { fallbackState: 'running' })
      this.upsertProcess(processing)
    },

    handleProcessingUpdated(payload: unknown): void {
      const parsed = parseProcessingEventPayload(payload)
      if (!parsed) {
        return
      }

      const existing = this.findProcessById(parsed.processingId)
      const processing = buildProcessingFromEvent(existing, parsed)
      this.upsertProcess(processing)
    },

    handleSentenceListRebuilt(payload: unknown): void {
      const parsed = parseSentenceListRebuiltPayload(payload)
      if (!parsed) {
        return
      }

      const existing = this.findProcessById(parsed.processingId)
      const processing = buildProcessingFromEvent(
        existing,
        {
          docId: parsed.docId,
          processingId: parsed.processingId,
          state: 'succeed',
          errorMessage: null,
        },
        {
          fallbackState: 'succeed',
        },
      )
      this.upsertProcess(processing)
    },

    async getAllProcesses(): Promise<ProcessItem[]> {
      this.loading = true
      this.error = null

      try {
        const processes = await get<ProcessItem[]>('/api/processes')
        this.processes = processes
        return processes
      } catch (error) {
        this.error = toErrorMessage(error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async segmentDocument(docId: string): Promise<SentenceSegmentationResponse> {
      this.loading = true
      this.error = null

      try {
        const response = await post<SentenceSegmentationResponse>(
          `/api/process/sentence_segmentation/${encodeURIComponent(docId)}`,
        )
        this.upsertProcess(response.processing)
        return response
      } catch (error) {
        this.error = toErrorMessage(error)
        throw error
      } finally {
        this.loading = false
      }
    },
  },
})
