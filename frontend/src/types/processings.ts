export type ProcessingType = 'sentence_segmentation' | 'lemma' | 'fvg' | 'import_rule'
export type ProcessingState = 'running' | 'succeed' | 'failed'

export interface ProcessingItem {
  id: string
  parent_id: string
  doc_id: string | null
  type: ProcessingType
  state: ProcessingState
  created_at: string
  updated_at: string
  error_message: string | null
  meta_json: string | null
  meta: Record<string, unknown> | null
}

export interface ImportRuleProcessRequest extends Record<string, unknown> {
  path: string
  type: 'fvg'
}

export interface SentenceSegmentationRequest extends Record<string, unknown> {
  doc_id: string
  preview_length: number
}

export interface LemmatizeRequest extends Record<string, unknown> {
  segmentation_id: string
}
