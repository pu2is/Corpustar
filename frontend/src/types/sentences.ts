import type { CursorItem } from '@/types/pagination'

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
  cursor: string | null
  limit: number
}

export interface SentenceMergeRequest extends Record<string, unknown> {
  sentence_ids: string[]
  limit?: number
}

export interface SentenceClipRequest extends Record<string, unknown> {
  sentence_id: string
  split_offset: number
  limit?: number
}

export interface CorrectSentenceRequest extends Record<string, unknown> {
  sentence_id: string
  corrected_text: string
  cursor: string | null
  limit: number
}

export interface SentenceListItem {
  prevSentence: SentenceItem | null
  sentences: SentenceItem[]
  cursor: CursorItem
  highlight: string[]
}
