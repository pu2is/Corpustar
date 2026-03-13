import { get, post } from '@/stores/fetchWrapper'
import type {
  ClipSentenceRequest,
  ClipSentenceResponse,
  MergeSentencesRequest,
  SentenceCursorPage,
  SentenceItem,
  SentenceSegmentationResponse,
} from '@/types/sentences'

function getSentenceSegmentationEndpoint(docId: string): string {
  return `/api/documents/${encodeURIComponent(docId)}/sentence-segmentations`
}

function getSentenceCursorPageEndpoint(docId: string): string {
  return `/api/documents/${encodeURIComponent(docId)}/sentences`
}

function getMergeSentenceEndpoint(): string {
  return '/api/sentences/merge'
}

function getClipSentenceEndpoint(sentenceId: string): string {
  return `/api/sentences/${encodeURIComponent(sentenceId)}/clip`
}

export function segmentDocumentSentences(docId: string): Promise<SentenceSegmentationResponse> {
  return post<SentenceSegmentationResponse>(getSentenceSegmentationEndpoint(docId))
}

export function getSentenceCursorPage(
  docId: string,
  processingId: string,
  afterStartOffset: number | null,
  limit: number,
): Promise<SentenceCursorPage> {
  return get<SentenceCursorPage>(
    getSentenceCursorPageEndpoint(docId),
    {
      params: {
        processingId,
        afterStartOffset,
        limit,
      },
    },
  )
}

export function mergeSentences(sentenceIds: string[]): Promise<SentenceItem> {
  const payload: MergeSentencesRequest = { sentenceIds }
  return post<SentenceItem>(getMergeSentenceEndpoint(), payload)
}

export function clipSentence(
  sentenceId: string,
  splitOffset: number,
): Promise<ClipSentenceResponse> {
  const payload: ClipSentenceRequest = { splitOffset }
  return post<ClipSentenceResponse>(getClipSentenceEndpoint(sentenceId), payload)
}
