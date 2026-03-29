import { defineStore } from 'pinia'

import { del, get, post } from '@/stores/fetchWrapper'
import { on } from '@/socket/socket'
import type { ProcessResponse, ProcessResponseWithId } from '@/types/general'
import type { ImportRuleProcessRequest } from '@/types/processings'
import type { RuleItem } from '@/types/rules'

export const useRuleStore = defineStore('rule-store', {
  state: () => ({
    rules: [] as RuleItem[],
    connected: false as boolean,
  }),
  getters: {},
  actions: {
    // 1. Socket binding
    bindSocketEvents(): void {
      if (this.connected) {
        return
      }
      on('socket:connected', async () => {
        this.connected = true
        this.rules = await this.getAllRules()
      })
      on('socket:disconnected', () => {
        this.connected = false
        this.rules = []
      })
      on('importRule:succeed', (socketMsg) => {
        const payload = socketMsg as { rule?: RuleItem }
        const rule = payload?.rule
        if (!rule) {
          return
        }

        const existingIndex = this.rules.findIndex((item) => item.id === rule.id)
        if (existingIndex >= 0) {
          this.rules.splice(existingIndex, 1, rule)
          return
        }

        this.rules.unshift(rule)
      })
      on('rule:removed', (socketMsg) => {
        const removedId = (socketMsg as { id?: string })?.id
        if (!removedId) {
          return
        }

        const removeIndex = this.rules.findIndex((rule) => rule.id === removedId)
        if (removeIndex >= 0) {
          this.rules.splice(removeIndex, 1)
        }
      })
    },

    // 2. API requests
    async getAllRules(): Promise<RuleItem[]> {
      const rules = await get<RuleItem[]>('/api/rule')
      this.rules = rules
      return rules
    },

    async removeRuleById(ruleId: string): Promise<ProcessResponseWithId> {
      return del<ProcessResponseWithId>(`/api/rule/${encodeURIComponent(ruleId)}`)
    },

    async importRule(payload: ImportRuleProcessRequest): Promise<ProcessResponse> {
      return post<ProcessResponse>('/api/process/import_rule', payload)
    },

    // 3. Helpers
    upsertRule(rule: RuleItem): void {
      const existingIndex = this.rules.findIndex((item) => item.id === rule.id)
      if (existingIndex >= 0) {
        this.rules.splice(existingIndex, 1, rule)
        return
      }

      this.rules.unshift(rule)
    },

    findRuleById(ruleId: string): RuleItem | null {
      return this.rules.find((item) => item.id === ruleId) ?? null
    },

    getRuleNameById(ruleId: string): string {
      const rule = this.findRuleById(ruleId)
      if (!rule?.path) {
        return ''
      }

      const fileNameWithExtension = rule.path.split(/[\\/]/).pop() ?? ''
      const extensionIndex = fileNameWithExtension.lastIndexOf('.')
      return extensionIndex > 0
        ? fileNameWithExtension.slice(0, extensionIndex)
        : fileNameWithExtension
    },

    // Backward-compatible alias
    getRuleByStoreId(ruleId: string): RuleItem | null {
      return this.findRuleById(ruleId)
    },
  },
})
