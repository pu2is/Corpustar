export interface LemmaItem {
  id: string
  docId: string
  segmentationId: string
  sentenceId: string
  sourceText: string
  lemmaText: string
  correctedLemma: string
  fvgResultId: string | null
}

export interface ActionResponse {
  succeed: boolean
  error_msg: string | null
}
