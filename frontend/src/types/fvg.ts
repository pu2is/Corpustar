export type StructureType = 'prep' | 'akku'

export interface FvgItem {
  id: string
  rule_id: string
  verb: string
  phrase: string
  noun: string
  prep: string
  structure_type: StructureType
  semantic_type: string
}

export interface FvgAppendRequest extends Record<string, unknown> {
  rule_id: string
  verb: string
  phrase: string
  noun?: string
  prep?: string
  structure_type?: StructureType
  semantic_type?: string
}

export interface FvgCorrectRequest extends Record<string, unknown> {
  id: string
  verb?: string
  phrase?: string
  noun?: string
  prep?: string
  structure_type?: StructureType
  semantic_type?: string
}
