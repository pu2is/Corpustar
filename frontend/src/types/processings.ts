export type ProcessingType =
  | 'sentence_segmentation'
  | 'lemmatize'
  | 'fvg_detection'
  | 'manual_sentence_edit'

export type ProcessingState = 'running' | 'succeed' | 'failed'

export interface ProcessingItem {
  id: string
  docId: string
  type: ProcessingType
  state: ProcessingState
  createdAt: string
  updatedAt: string
  errorMessage: string | null
  meta: Record<string, unknown> | null
}
