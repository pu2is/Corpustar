import { defineStore } from 'pinia'
import { del, get, patch, post } from '@/stores/fetchWrapper'
import { on } from '@/socket/socket'
// types
import type { AddFvgRuleRequest, RemoveFvgRuleResponse, RuleFvgItem, UpdateFvgRuleRequest } from '@/types/rules'

export const useRuleFvgStore = defineStore('rule-fvg-store', {
  state: () => ({
    activeRuleId: '' as string,
    fvgRules: [] as RuleFvgItem[],
    connected: false,
    hasBoundSocketEvents: false,
  }),
  getters: {
    getFvgRuleById: (state) => (fvgRuleId: string): RuleFvgItem | null => {
      if (!fvgRuleId) {
        return null
      }

      return state.fvgRules.find((item) => item.id === fvgRuleId) ?? null
    },
  },
  actions: {
    bindSocketEvents(): void {
      if (this.hasBoundSocketEvents) {
        return
      }

      on('socket:connected', () => {
        this.connected = true
      })
      on('socket:disconnected', () => {
        this.connected = false
      })
      on('fvgRules:created', (payload) => {
        if (Array.isArray(payload)) {
          const items = payload
            .map((item) => {
              if (typeof item !== 'object' || item === null) {
                return null
              }

              const rawItem = item as Record<string, unknown>
              const id = typeof rawItem.id === 'string' ? rawItem.id.trim() : ''
              const ruleId = typeof rawItem.ruleId === 'string' ? rawItem.ruleId.trim() : ''
              const verb = typeof rawItem.verb === 'string' ? rawItem.verb.trim() : ''
              const phrase = typeof rawItem.phrase === 'string' ? rawItem.phrase.trim() : ''

              if (!id || !ruleId || !verb || !phrase) {
                return null
              }

              return { id, ruleId, verb, phrase }
            })
            .filter((item): item is RuleFvgItem => item !== null)

          this.fvgRules = items
          return
        }

        if (typeof payload !== 'object' || payload === null) {
          return
        }

        const rawPayload = payload as Record<string, unknown>
        const ruleId = typeof rawPayload.ruleId === 'string' ? rawPayload.ruleId.trim() : ''

        if (Array.isArray(rawPayload.items)) {
          if (ruleId && this.activeRuleId !== ruleId) {
            return
          }

          const items = rawPayload.items
            .map((item) => {
              if (typeof item !== 'object' || item === null) {
                return null
              }

              const rawItem = item as Record<string, unknown>
              const id = typeof rawItem.id === 'string' ? rawItem.id.trim() : ''
              const itemRuleId = typeof rawItem.ruleId === 'string' ? rawItem.ruleId.trim() : ''
              const verb = typeof rawItem.verb === 'string' ? rawItem.verb.trim() : ''
              const phrase = typeof rawItem.phrase === 'string' ? rawItem.phrase.trim() : ''

              if (!id || !itemRuleId || !verb || !phrase) {
                return null
              }

              return { id, ruleId: itemRuleId, verb, phrase }
            })
            .filter((item): item is RuleFvgItem => item !== null)

          this.fvgRules = items
          return
        }

        if (!ruleId || this.activeRuleId !== ruleId) {
          return
        }

        void this.getAllFvgRuleByRuleId(ruleId).catch(() => undefined)
      })
      on('fvgRules:removed', (payload) => {
        if (typeof payload === 'object' && payload !== null) {
          const rawPayload = payload as Record<string, unknown>
          const ruleId = typeof rawPayload.ruleId === 'string' ? rawPayload.ruleId.trim() : ''

          if (ruleId && this.activeRuleId !== ruleId) {
            return
          }

          if (ruleId && this.activeRuleId === ruleId) {
            this.activeRuleId = ''
          }
        }

        this.fvgRules = []
      })
      on('fvgRule:appended', (payload) => {
        if (typeof payload !== 'object' || payload === null) {
          return
        }

        const rawItem = payload as Record<string, unknown>
        const id = typeof rawItem.id === 'string' ? rawItem.id.trim() : ''
        const ruleId = typeof rawItem.ruleId === 'string' ? rawItem.ruleId.trim() : ''
        const verb = typeof rawItem.verb === 'string' ? rawItem.verb.trim() : ''
        const phrase = typeof rawItem.phrase === 'string' ? rawItem.phrase.trim() : ''

        if (!id || !ruleId || !verb || !phrase) {
          return
        }

        if (!this.activeRuleId || ruleId !== this.activeRuleId) {
          return
        }

        this.upsertFvgRule({ id, ruleId, verb, phrase })
      })
      on('fvgRule:removed', (payload) => {
        if (typeof payload !== 'object' || payload === null) {
          return
        }

        const rawPayload = payload as Record<string, unknown>
        const id = typeof rawPayload.id === 'string' ? rawPayload.id.trim() : ''
        const ruleId = typeof rawPayload.ruleId === 'string' ? rawPayload.ruleId.trim() : ''

        if (!id) {
          return
        }

        if (ruleId && this.activeRuleId && ruleId !== this.activeRuleId) {
          return
        }

        this.removeFvgRuleFromStore(id)
      })
      // Support both backend event name and requested event spelling.
      on('fvgRule:updated', (payload) => {
        if (typeof payload !== 'object' || payload === null) {
          return
        }

        const rawItem = payload as Record<string, unknown>
        const id = typeof rawItem.id === 'string' ? rawItem.id.trim() : ''
        const ruleId = typeof rawItem.ruleId === 'string' ? rawItem.ruleId.trim() : ''
        const verb = typeof rawItem.verb === 'string' ? rawItem.verb.trim() : ''
        const phrase = typeof rawItem.phrase === 'string' ? rawItem.phrase.trim() : ''

        if (!id || !ruleId || !verb || !phrase) {
          return
        }

        if (!this.activeRuleId || ruleId !== this.activeRuleId) {
          return
        }

        this.upsertFvgRule({ id, ruleId, verb, phrase })
      })
      on('fvgRule:update', (payload) => {
        if (typeof payload !== 'object' || payload === null) {
          return
        }

        const rawItem = payload as Record<string, unknown>
        const id = typeof rawItem.id === 'string' ? rawItem.id.trim() : ''
        const ruleId = typeof rawItem.ruleId === 'string' ? rawItem.ruleId.trim() : ''
        const verb = typeof rawItem.verb === 'string' ? rawItem.verb.trim() : ''
        const phrase = typeof rawItem.phrase === 'string' ? rawItem.phrase.trim() : ''

        if (!id || !ruleId || !verb || !phrase) {
          return
        }

        if (!this.activeRuleId || ruleId !== this.activeRuleId) {
          return
        }

        this.upsertFvgRule({ id, ruleId, verb, phrase })
      })

      this.hasBoundSocketEvents = true
    },

    setActiveRuleId(ruleId: string): void {
      this.activeRuleId = ruleId

      if (!ruleId) {
        this.fvgRules = []
      }
    },

    // Get
    async getAllFvgRuleByRuleId(ruleId: string): Promise<RuleFvgItem[]> {
      this.activeRuleId = ruleId

      const requestedRuleId = ruleId
      const items = await get<RuleFvgItem[]>(`/api/rules/fvg/${encodeURIComponent(ruleId)}`)
      if (this.activeRuleId === requestedRuleId) {
        this.fvgRules = items
      }

      return items
    },

    // Post
    async addFvgRule(payload: AddFvgRuleRequest): Promise<RuleFvgItem> {
      const item = await post<RuleFvgItem>('/api/rules/add-fvg', payload)
      return item
    },

    // Delete
    async removerFvgRule(fvgRuleId: string): Promise<RemoveFvgRuleResponse> {
      const response = await del<RemoveFvgRuleResponse>(`/api/rules/rm-fvg/${encodeURIComponent(fvgRuleId)}`)
      return response
    },

    // Patch
    async modifyFvgRule(fvgRuleId: string, payload: UpdateFvgRuleRequest): Promise<RuleFvgItem> {
      const item = await patch<RuleFvgItem>(`/api/rules/fvg/${encodeURIComponent(fvgRuleId)}`, payload)
      this.upsertFvgRule(item)
      return item
    },

    upsertFvgRule(item: RuleFvgItem): void {
      const existingIndex = this.fvgRules.findIndex((existingItem) => existingItem.id === item.id)
      if (existingIndex >= 0) {
        this.fvgRules.splice(existingIndex, 1, item)
        return
      }

      this.fvgRules.push(item)
    },

    removeFvgRuleFromStore(fvgRuleId: string): void {
      this.fvgRules = this.fvgRules.filter((item) => item.id !== fvgRuleId)
    },
  },
})
