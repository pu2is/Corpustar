export interface SentenceItem {
  id: string
  version_id: string
  doc_id: string
  start_offset: number
  end_offset: number
  source_text: string
  corrected_text: string
}

export interface CollectSentenceRequest extends Record<string, unknown> {
  doc_id: string
  segmentation_id: string
  split_offset: number | null
  limit: number
}

export interface SentenceMergeRequest extends Record<string, unknown> {
  sentence_ids: string[]
}

export interface SentenceClipRequest extends Record<string, unknown> {
  sentence_id: string
  split_offset: number
}

export interface CorrectSentenceRequest extends Record<string, unknown> {
  sentence_id: string
  corrected_text: string
}

export interface SentenceMergedSocketPayload {
  result: SentenceItem
  meta: SentenceMergeRequest
}

export interface SentenceClippedSocketPayload {
  result: SentenceItem[]
  meta: SentenceClipRequest
}

export interface SentenceCursorPage {
  items: SentenceItem[]
  next_after_start_offset: number | null
  has_more: boolean
}
