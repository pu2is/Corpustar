import { defineStore } from 'pinia'

import { del, get, post } from '@/stores/fetchWrapper'
import { on } from '@/socket/socket'
import type { FvgAppendRequest, FvgCorrectRequest, FvgItem } from '@/types/fvg'
import type { ProcessResponseWithId } from '@/types/general'

export const useRuleFvgStore = defineStore('rule-fvg-store', {
  state: () => ({
    fvg: [] as FvgItem[],
    fvgDict: {} as Record<string, FvgItem[]>,
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
      on('fvg:removed', (socketMsg) => {
        const removedId = (socketMsg as { id?: string })?.id
        if (!removedId) {
          return
        }

        const removeIndex = this.fvg.findIndex((item) => item.id === removedId)
        if (removeIndex >= 0) {
          this.fvg.splice(removeIndex, 1)
        }
      })
      on('fvg:updated', (socketMsg) => {
        const payload = socketMsg as FvgItem
        const targetIndex = this.fvg.findIndex((item) => item.id === payload.id)
        if (targetIndex >= 0) {
          this.fvg.splice(targetIndex, 1, payload)
          return
        }

        this.fvg.push(payload)
      })
      on('fvg:appended', (socketMsg) => {
        const payload = socketMsg as FvgItem
        const existingIndex = this.fvg.findIndex((item) => item.id === payload.id)
        if (existingIndex >= 0) {
          this.fvg.splice(existingIndex, 1, payload)
          return
        }

        this.fvg.push(payload)
      })
    },

    // 2. API requests
    async getFvgByRuleId(ruleId: string): Promise<FvgItem[]> {
      const items = await get<FvgItem[]>(`/api/fvg/${encodeURIComponent(ruleId)}`)
      this.fvg = items
      return items
    },

    async getFvgByVerb(ruleId: string, verb: string): Promise<FvgItem[]> {
      const items = await post<FvgItem[]>('/api/fvg/by_verb', { rule_id: ruleId, verb })
      this.fvgDict[verb] = items
      return items
    },

    async appendFvg(payload: FvgAppendRequest): Promise<ProcessResponseWithId> {
      return post<ProcessResponseWithId>('/api/fvg/append', payload)
    },

    async correctFvg(payload: FvgCorrectRequest): Promise<ProcessResponseWithId> {
      return post<ProcessResponseWithId>('/api/fvg/correct', payload)
    },

    async removeFvgById(fvgId: string): Promise<ProcessResponseWithId> {
      return del<ProcessResponseWithId>(`/api/fvg/${encodeURIComponent(fvgId)}`)
    },

    // 3. Helpers
    upsertFvg(item: FvgItem): void {
      const existingIndex = this.fvg.findIndex((entry) => entry.id === item.id)
      if (existingIndex >= 0) {
        this.fvg.splice(existingIndex, 1, item)
        return
      }

      this.fvg.push(item)
    },

    findFvgById(fvgId: string): FvgItem | null {
      return this.fvg.find((item) => item.id === fvgId) ?? null
    },

    clearFvgDict(): void {
      this.fvgDict = {}
    },

    // Backward-compatible aliases
    getAllFvgRuleByRuleId(ruleId: string): Promise<FvgItem[]> {
      return this.getFvgByRuleId(ruleId)
    },

    addFvgRule(payload: { ruleId: string; verb: string; phrase: string }): Promise<ProcessResponseWithId> {
      return this.appendFvg({
        rule_id: payload.ruleId,
        verb: payload.verb,
        phrase: payload.phrase,
      })
    },

    modifyFvgRule(fvgId: string, payload: { verb?: string; phrase?: string }): Promise<ProcessResponseWithId> {
      return this.correctFvg({
        id: fvgId,
        verb: payload.verb,
        phrase: payload.phrase,
      })
    },

    removerFvgRule(fvgRuleId: string): Promise<ProcessResponseWithId> {
      return this.removeFvgById(fvgRuleId)
    },

    setActiveRuleId(_ruleId: string): void {
      // no-op for backward compatibility
    },
  },
})
