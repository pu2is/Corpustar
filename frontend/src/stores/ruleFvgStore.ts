import { defineStore } from 'pinia'

import { del, get, patch, post } from '@/stores/fetchWrapper'
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

export interface RuleFvgItem {
  id: string
  ruleId: string
  verb: string
  phrase: string
}

export type AddFvgRuleRequest = {
  ruleId: string
  verb: string
  phrase: string
}

export type UpdateFvgRuleRequest = {
  verb: string
  phrase: string
}

export interface RemoveFvgRuleResponse {
  id: string
  ruleId?: string | null
}

interface RuleFvgState {
  fvgRules: RuleFvgItem[]
  connected: boolean
}

interface FvgRulesCreatedSocketPayload {
  ruleId: string | null
  items: RuleFvgItem[] | null
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

function toRuleFvgItem(value: unknown): RuleFvgItem | null {
  if (!isRecord(value)) {
    return null
  }

  const id = toNonEmptyString(value.id)
  const ruleId = toNonEmptyString(value.ruleId)
  const verb = toNonEmptyString(value.verb)
  const phrase = toNonEmptyString(value.phrase)
  if (!id || !ruleId || !verb || !phrase) {
    return null
  }

  return {
    id,
    ruleId,
    verb,
    phrase,
  }
}

function toFvgRulesCreatedPayload(payload: unknown): FvgRulesCreatedSocketPayload | null {
  if (Array.isArray(payload)) {
    const items = payload.map(toRuleFvgItem).filter((item): item is RuleFvgItem => item !== null)
    return {
      ruleId: null,
      items,
    }
  }

  if (!isRecord(payload)) {
    return null
  }

  const ruleId = toNonEmptyString(payload.ruleId)
  const rawItems = Array.isArray(payload.items) ? payload.items : null
  const items = rawItems
    ? rawItems.map(toRuleFvgItem).filter((item): item is RuleFvgItem => item !== null)
    : null

  return {
    ruleId,
    items,
  }
}

function toRemovedRuleId(payload: unknown): string | null {
  if (!isRecord(payload)) {
    return null
  }

  return toNonEmptyString(payload.id)
}

export const useRuleFvgStore = defineStore('rule-fvg-store', {
  state: (): RuleFvgState => ({
    fvgRules: [],
    connected: false,
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
      if (hasBoundSocketEvents) {
        return
      }

      on(SOCKET_CONNECTED_EVENT, () => {
        this.connected = true
      })
      on(SOCKET_DISCONNECTED_EVENT, () => {
        this.connected = false
      })
      on('fvgRules:created', (payload) => {
        this.handleFvgRulesCreated(payload)
      })
      on('fvgRules:removed', () => {
        this.handleFvgRulesRemoved()
      })
      on('fvgRule:appended', (payload) => {
        this.handleFvgRuleAppended(payload)
      })
      on('fvgRule:removed', (payload) => {
        this.handleFvgRuleRemoved(payload)
      })
      // Support both backend event name and requested event spelling.
      on('fvgRule:updated', (payload) => {
        this.handleFvgRuleUpdated(payload)
      })
      on('fvgRule:update', (payload) => {
        this.handleFvgRuleUpdated(payload)
      })

      hasBoundSocketEvents = true
    },

    // Rules API
    async getAllRules(): Promise<RuleItem[]> {
      return get<RuleItem[]>('/api/rules')
    },

    async getRuleById(ruleId: string): Promise<RuleItem | null> {
      const rule = await get<RuleItem | null>(`/api/rules/${encodeURIComponent(ruleId)}`)
      if (rule) {
        const parsed = toRuleItem(rule)
        if (!parsed) {
          return null
        }
      }
      return rule
    },

    async importRules(payload: ImportRuleRequest): Promise<RuleItem> {
      return post<RuleItem>('/api/rules', payload)
    },

    async removeRuleById(ruleId: string): Promise<RemoveRuleResponse> {
      return del<RemoveRuleResponse>(`/api/rules/${encodeURIComponent(ruleId)}`)
    },

    // FVG rules API
    async getAllFvgRuleByRuleId(ruleId: string): Promise<RuleFvgItem[]> {
      const items = await get<RuleFvgItem[]>(`/api/rules/fvg/${encodeURIComponent(ruleId)}`)
      this.fvgRules = items
      return items
    },

    async addFvgRule(payload: AddFvgRuleRequest): Promise<RuleFvgItem> {
      const item = await post<RuleFvgItem>('/api/rules/add-fvg', payload)
      this.upsertFvgRule(item)
      return item
    },

    async removerFvgRule(fvgRuleId: string): Promise<RemoveFvgRuleResponse> {
      const response = await del<RemoveFvgRuleResponse>(`/api/rules/rm-fvg/${encodeURIComponent(fvgRuleId)}`)
      this.removeFvgRuleFromStore(response.id)
      return response
    },

    async modifyFvgRule(fvgRuleId: string, payload: UpdateFvgRuleRequest): Promise<RuleFvgItem> {
      const item = await patch<RuleFvgItem>(`/api/rules/fvg/${encodeURIComponent(fvgRuleId)}`, payload)
      this.upsertFvgRule(item)
      return item
    },

    // Socket event handlers
    handleFvgRulesCreated(payload: unknown): void {
      const parsed = toFvgRulesCreatedPayload(payload)
      if (!parsed) {
        return
      }

      if (parsed.items !== null) {
        this.fvgRules = parsed.items
        return
      }

      if (!parsed.ruleId) {
        return
      }

      void this.getAllFvgRuleByRuleId(parsed.ruleId).catch(() => undefined)
    },

    handleFvgRulesRemoved(): void {
      this.fvgRules = []
    },

    handleFvgRuleAppended(payload: unknown): void {
      const item = toRuleFvgItem(payload)
      if (!item) {
        return
      }

      this.upsertFvgRule(item)
    },

    handleFvgRuleRemoved(payload: unknown): void {
      const fvgRuleId = toRemovedRuleId(payload)
      if (!fvgRuleId) {
        return
      }

      this.removeFvgRuleFromStore(fvgRuleId)
    },

    handleFvgRuleUpdated(payload: unknown): void {
      const item = toRuleFvgItem(payload)
      if (!item) {
        return
      }

      this.upsertFvgRule(item)
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
