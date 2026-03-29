export type RuleType = 'fvg'

export interface RuleItem {
  id: string
  version_id: string
  type: RuleType
  path: string
}
