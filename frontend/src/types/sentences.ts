import type { ProcessingItem } from '@/types/processings'

export interface SentenceItem {
  id: string
  docId: string
  processingId: string
  startOffset: number
  endOffset: number
  text: string
  lemmaText: string | null
}

export interface SentenceCursorPage {
  items: SentenceItem[]
  nextAfterStartOffset: number | null
  hasMore: boolean
}

export interface SentenceSegmentationResultSnapshot {
  processing: ProcessingItem | null
  sentenceCount: number
  preview: SentenceItem[]
}

export interface SentenceSegmentationResponse extends SentenceSegmentationResultSnapshot {
  processing: ProcessingItem
}

export interface MergeSentencesRequest extends Record<string, unknown> {
  sentenceIds: string[]
}

export interface ClipSentenceRequest extends Record<string, unknown> {
  splitOffset: number
}

export interface ClipSentenceResponse {
  items: SentenceItem[]
}
