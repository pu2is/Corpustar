import { defineStore } from 'pinia'

import { del, get, post } from '@/stores/fetchWrapper'
import { on, SOCKET_CONNECTED_EVENT, SOCKET_DISCONNECTED_EVENT } from '@/socket/socket'

type RuleType = 'fvg'

export interface RuleItem {
  id: string
  type: RuleType
  path: string
}

export type ImportRuleRequest = {
  path: string
  type?: RuleType
}

export interface RemoveRuleResponse {
  id: string
  removedFvgCount?: number | null
}

interface RuleState {
  rules: RuleItem[]
  connected: boolean
}

// Keep socket lifecycle in socket.ts; store only consumes events.
let hasBoundSocketEvents = false

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

function toRuleType(value: unknown): RuleType | null {
  return value === 'fvg' ? value : null
}

function toRuleItem(value: unknown): RuleItem | null {
  if (!isRecord(value)) {
    return null
  }

  const id = toNonEmptyString(value.id)
  const path = toNonEmptyString(value.path)
  const type = toRuleType(value.type)
  if (!id || !path || !type) {
    return null
  }

  return {
    id,
    type,
    path,
  }
}

function toRemovedRuleId(value: unknown): string | null {
  if (!isRecord(value)) {
    return null
  }

  return toNonEmptyString(value.id)
}

export const useRuleStore = defineStore('rule-store', {
  state: (): RuleState => ({
    rules: [],
    connected: false,
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
      if (hasBoundSocketEvents) {
        return
      }

      on(SOCKET_CONNECTED_EVENT, () => {
        this.connected = true
        void this.getAllRules().catch(() => undefined)
      })
      on(SOCKET_DISCONNECTED_EVENT, () => {
        this.connected = false
      })
      on('rule:created', (payload) => {
        this.handleRuleCreated(payload)
      })
      on('rule:removed', (payload) => {
        this.handleRuleRemoved(payload)
      })

      hasBoundSocketEvents = true
    },

    async getAllRules(): Promise<RuleItem[]> {
      const rules = await get<RuleItem[]>('/api/rules')
      this.rules = rules
      return rules
    },

    async getRuleById(ruleId: string): Promise<RuleItem | null> {
      const rule = await get<RuleItem | null>(`/api/rules/${encodeURIComponent(ruleId)}`)
      if (rule) {
        this.upsertRule(rule)
      }
      return rule
    },

    async importRules(payload: ImportRuleRequest): Promise<RuleItem> {
      const rule = await post<RuleItem>('/api/rules', payload)
      this.upsertRule(rule)
      return rule
    },

    async removeRuleById(ruleId: string): Promise<RemoveRuleResponse> {
      const response = await del<RemoveRuleResponse>(`/api/rules/${encodeURIComponent(ruleId)}`)
      this.removeRuleFromStore(response.id)
      return response
    },

    handleRuleCreated(payload: unknown): void {
      const rule = toRuleItem(payload)
      if (!rule) {
        return
      }

      this.upsertRule(rule)
    },

    handleRuleRemoved(payload: unknown): void {
      const ruleId = toRemovedRuleId(payload)
      if (!ruleId) {
        return
      }

      this.removeRuleFromStore(ruleId)
    },

    upsertRule(rule: RuleItem): void {
      const existingIndex = this.rules.findIndex((existingRule) => existingRule.id === rule.id)
      if (existingIndex >= 0) {
        this.rules.splice(existingIndex, 1, rule)
        return
      }

      this.rules.push(rule)
    },

    removeRuleFromStore(ruleId: string): void {
      this.rules = this.rules.filter((rule) => rule.id !== ruleId)
    },
  },
})
