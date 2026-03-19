import { defineStore } from 'pinia'
import { get, post } from '@/stores/fetchWrapper'
import { on } from '@/socket/socket'
import type { ClipSentenceResponse, SentenceCursorPage, SentenceItem} from '@/types/sentences'

interface SentenceState {
  itemsByDocProcessKey: Record<string, SentenceItem[]>
  loadingByDocProcessKey: Record<string, boolean>
  errorByDocProcessKey: Record<string, string | null>
}

interface GetSentenceOptions {
  afterStartOffset?: number | null
  limit?: number
  append?: boolean
}

interface DocProcessPayload {
  docId: string
  processingId: string
}

// Keep socket lifecycle in socket.ts; store only consumes events.
let hasBoundSocketEvents = false

function toErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

function toNonEmptyString(value: unknown): string | null {
  if (typeof value !== 'string') {
    return null
  }

  const trimmed = value.trim()
  return trimmed.length ? trimmed : null
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function toDocProcessPayload(payload: unknown): DocProcessPayload | null {
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

function uniqueNonEmptySentenceIds(sentenceIds: string[]): string[] {
  const seen = new Set<string>()
  const normalized: string[] = []

  for (const sentenceId of sentenceIds) {
    if (!sentenceId || seen.has(sentenceId)) {
      continue
    }

    seen.add(sentenceId)
    normalized.push(sentenceId)
  }

  return normalized
}

function getSentenceKey(docId: string, processId: string): string {
  return `${docId}::${processId}`
}

export const useSentenceStore = defineStore('sentence-store', {
  state: (): SentenceState => ({
    itemsByDocProcessKey: {},
    loadingByDocProcessKey: {},
    errorByDocProcessKey: {},
  }),
  getters: {
    getSentenceItems: (state) => (docId: string, processId: string): SentenceItem[] => {
      if (!docId || !processId) {
        return []
      }

      const key = getSentenceKey(docId, processId)
      return state.itemsByDocProcessKey[key] ?? []
    },
    isSentenceLoading: (state) => (docId: string, processId: string): boolean => {
      if (!docId || !processId) {
        return false
      }

      const key = getSentenceKey(docId, processId)
      return state.loadingByDocProcessKey[key] ?? false
    },
  },
  actions: {
    bindSocketEvents(): void {
      if (hasBoundSocketEvents) {
        return
      }

      on('sentence:merged', (payload) => {
        this.handleSentenceChanged(payload)
      })
      on('sentence:clipped', (payload) => {
        this.handleSentenceChanged(payload)
      })
      hasBoundSocketEvents = true
    },

    // Get
    async getSentences(docId: string, processId: string, options: GetSentenceOptions = {}): Promise<SentenceCursorPage> {
      const key = getSentenceKey(docId, processId)
      const afterStartOffset = options.afterStartOffset ?? null
      const limit = options.limit ?? 20
      const append = options.append ?? false

      this.loadingByDocProcessKey[key] = true
      this.errorByDocProcessKey[key] = null

      try {
        const page = await get<SentenceCursorPage>(
          `/api/sentences/${encodeURIComponent(docId)}`,
          {
            params: {
              processingId: processId,
              afterStartOffset,
              limit,
            },
          },
        )

        const nextItems = page.items ?? []
        if (!append) {
          this.itemsByDocProcessKey[key] = nextItems
          return page
        }

        const existingItems = this.itemsByDocProcessKey[key] ?? []
        const existingIds = new Set(existingItems.map((item) => item.id))
        const dedupedNextItems = nextItems.filter((item) => !existingIds.has(item.id))
        this.itemsByDocProcessKey[key] = [...existingItems, ...dedupedNextItems]

        return page
      } catch (error) {
        this.errorByDocProcessKey[key] = toErrorMessage(error)
        throw error
      } finally {
        this.loadingByDocProcessKey[key] = false
      }
    },

    // Post: merge
    async mergeSentences(sentenceIds: string[]): Promise<SentenceItem> {
      const normalizedSentenceIds = uniqueNonEmptySentenceIds(sentenceIds)
      if (normalizedSentenceIds.length < 2) {
        throw new Error('At least two sentence IDs are required for merge.')
      }

      const mergedItem = await post<SentenceItem>('/api/sentences/merge', {
        sentenceIds: normalizedSentenceIds,
      })
      return mergedItem
    },

    // Post: clip
    async clipSentence(sentenceId: string, splitOffset: number): Promise<SentenceItem[]> {
      const response = await post<ClipSentenceResponse>(
        `/api/sentences/${encodeURIComponent(sentenceId)}/clip`,
        { splitOffset },
      )
      return response.items ?? []
    },

    // Socket event handler
    handleSentenceChanged(payload: unknown): void {
      const parsed = toDocProcessPayload(payload)
      if (!parsed) {
        return
      }

      void this.refreshLoadedSentences(parsed.docId, parsed.processingId).catch(() => undefined)
    },

    async refreshLoadedSentences(docId: string, processId: string): Promise<SentenceCursorPage> {
      const key = getSentenceKey(docId, processId)
      const existingItems = this.itemsByDocProcessKey[key] ?? []
      const limit = Math.max(existingItems.length, 20)

      return this.getSentences(docId, processId, {
        afterStartOffset: null,
        limit,
        append: false,
      })
    },
  },
})
