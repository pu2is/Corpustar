export type RuleType = 'fvg'

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
