export interface LemmaItem {
  id: string
  version_id: string
  sentence_id: string
  source_word: string
  lemma_word: string
  word_index: number
  head_index: number
  pos_tag: string
  fine_pos_tag: string
  morph: string
  dependency_relationship: string
}

export interface GetLemmaRequest extends Record<string, unknown> {
  sentence_ids: string[]
}

export type GetLemmaResponse = Record<string, LemmaItem[]>

export interface LemmaViewItem {
  id: string
  segmentation_id: string
  sentence_id: string
  source_text: string
  lemma_text: string
}
