import { defineStore } from 'pinia'

import { del, get, post } from '@/stores/fetchWrapper'
import { SOCKET_EVENT } from '@/socket/events'
import { on } from '@/socket/socket'
import type { ProcessResponse, ProcessResponseWithId } from '@/types/general'
import type { ImportRuleProcessRequest } from '@/types/processings'
import type { RuleItem } from '@/types/rules'

export const useRuleStore = defineStore('rule-store', {
  state: () => ({
    rules: [] as RuleItem[],
    connected: false as boolean,
    socketBound: false as boolean,
  }),
  getters: {
    findRuleById: (state) => (ruleId: string) => {
      return state.rules.find((item) => item.id === ruleId) ?? null
    },
    getRuleNameById: (state) => (ruleId: string) => {
      const rule = state.rules.find((item) => item.id === ruleId) ?? null
      if (!rule?.path) {
        return ''
      }

      const fileNameWithExtension = rule.path.split(/[\\/]/).pop() ?? ''
      const extensionIndex = fileNameWithExtension.lastIndexOf('.')
      return extensionIndex > 0
        ? fileNameWithExtension.slice(0, extensionIndex)
        : fileNameWithExtension
    },
  },
  actions: {
    // 1. Socket binding
    bindSocketEvents(): void {
      if (this.socketBound) {
        return
      }
      this.socketBound = true

      on('socket:connected', async () => {
        this.connected = true
        this.rules = await this.getAllRules()
      })
      on('socket:disconnected', () => {
        this.connected = false
        this.rules = []
      })
      on(SOCKET_EVENT.IMPORT_RULE_SUCCEED, (socketMsg) => {
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
      on(SOCKET_EVENT.RULE_REMOVED, (socketMsg) => {
        const removedId = (socketMsg as { id?: string })?.id
        if (!removedId) {
          return
        }

        const removeIndex = this.rules.findIndex((rule) => rule.id === removedId)
        if (removeIndex >= 0) {
          this.rules.splice(removeIndex, 1)
        }
      })
      on(SOCKET_EVENT.RULE_COPY_FINISHED, (socketMsg) => {
        const payload = socketMsg as { ok?: boolean; item?: RuleItem }
        if (!payload.ok || !payload.item) {
          return
        }

        this.rules.unshift(payload.item)
      })
    },

    // 2. API requests
    async getAllRules(): Promise<RuleItem[]> {
      const rules = await get<RuleItem[]>('/api/rule')
      this.rules = rules
      return rules
    },

    async removeRuleById(ruleId: string): Promise<ProcessResponseWithId> {
      const response = await del<ProcessResponseWithId>(`/api/rule/${encodeURIComponent(ruleId)}`)
      if (response.ok) {
        const removeIndex = this.rules.findIndex((rule) => rule.id === response.id)
        if (removeIndex >= 0) {
          this.rules.splice(removeIndex, 1)
        }
      }
      return response
    },

    async cloneRule(ruleId: string): Promise<{ ok: boolean; err_msg: string }> {
      const result = await post<{ ok: boolean; err_msg: string }>(`/api/rule/clone/${encodeURIComponent(ruleId)}`)
      if (result.ok) {
        // Reload rules to show the cloned rule immediately
        this.rules = await this.getAllRules()
      }
      return result
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
  },
})
