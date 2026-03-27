import { defineStore } from 'pinia'

import { del, get, post } from '@/stores/fetchWrapper'
import { on } from '@/socket/socket'
import type { ImportRuleRequest, RemoveRuleResponse, RuleItem, RuleType } from '@/types/rules'

export const useRuleStore = defineStore('rule-store', {
  state: () => ({
    rules: [] as RuleItem[],
    connected: false,
    hasBoundSocketEvents: false,
  }),
  getters: {
    getRuleByStoreId: (state) => (ruleId: string): RuleItem | null => {
      if (!ruleId) {
        return null
      }

      return state.rules.find((rule) => rule.id === ruleId) ?? null
    },
  },
  actions: {
    bindSocketEvents(): void {
      if (this.hasBoundSocketEvents) {
        return
      }

      on('socket:connected', () => {
        this.connected = true
        void this.getAllRules().catch(() => undefined)
      })
      on('socket:disconnected', () => {
        this.connected = false
      })
      on('rule:created', (payload) => {
        if (typeof payload !== 'object' || payload === null) {
          return
        }

        const rawRule = payload as Record<string, unknown>
        const id = typeof rawRule.id === 'string' ? rawRule.id.trim() : ''
        const path = typeof rawRule.path === 'string' ? rawRule.path.trim() : ''
        const type = rawRule.type === 'fvg' ? (rawRule.type as RuleType) : null

        if (!id || !path || !type) {
          return
        }

        this.upsertRule({ id, type, path})
      })
      on('rule:removed', (payload) => {
        if (typeof payload !== 'object' || payload === null) {
          return
        }

        const rawRule = payload as Record<string, unknown>
        const ruleId = typeof rawRule.id === 'string' ? rawRule.id.trim() : ''
        if (!ruleId) {
          return
        }

        this.removeRuleFromStore(ruleId)
      })

      this.hasBoundSocketEvents = true
    },

    // Get
    async getAllRules(): Promise<RuleItem[]> {
      const rules = await get<RuleItem[]>('/api/rules')
      this.rules = rules
      return rules
    },

    // Get by Id
    async getRuleById(ruleId: string): Promise<RuleItem | null> {
      const rule = await get<RuleItem | null>(`/api/rules/${encodeURIComponent(ruleId)}`)
      return rule
    },

    // Post: import & create
    async importRules(payload: ImportRuleRequest): Promise<RuleItem> {
      const rule = await post<RuleItem>('/api/rules', payload)
      return rule
    },

    // Delete
    async removeRuleById(ruleId: string): Promise<RemoveRuleResponse> {
      const response = await del<RemoveRuleResponse>(`/api/rules/${encodeURIComponent(ruleId)}`)
      return response
    },

    upsertRule(rule: RuleItem): void {
      const existingIndex = this.rules.findIndex((existingRule) => existingRule.id === rule.id)
      if (existingIndex >= 0) {
        this.rules.splice(existingIndex, 1, rule)
        return
      }

      this.rules.unshift(rule)
    },

    removeRuleFromStore(ruleId: string): void {
      this.rules = this.rules.filter((rule) => rule.id !== ruleId)
    },
  },
})
