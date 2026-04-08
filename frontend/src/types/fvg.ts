import type { SentenceItem } from '@/types/sentences'
import type { LemmaItem } from '@/types/lemmatize'

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

export interface FvgCandidateItem {
  id: string
  sentence_id: string
  process_id: string
  algo_fvg_entry_id: string
  corrected_fvg_entry_id: string
  algo_verb_token: string
  algo_verb_index: number
  corrected_verb_token: string
  corrected_verb_index: number
  algo_noun_token: string
  algo_noun_index: number
  corrected_noun_token: string
  corrected_noun_index: number
  algo_prep_token: string
  algo_prep_index: number
  corrected_prep_token: string
  corrected_prep_index: number
  label: string
  manuelle_created: boolean
  removed: boolean
}

export interface SentenceFvgItem extends SentenceItem {
  fvg_candidates: FvgCandidateItem[]
  lemma_tokens: LemmaItem[]
  highlight_lemma: LemmaItem[]
}

export interface FvgCursorItem {
  currentCursor: string | null
  nextCursor: string | null
  previousCursor: string | null
}

export interface SentenceFvgListResponse {
  sentences: SentenceFvgItem[]
  cursor: FvgCursorItem
}

export interface FvgCandidateListRequest extends Record<string, unknown> {
  segmentation_id: string
  cursor: string | null
  limit: number
  verb_filter?: string | null
}

export interface FvgCandidateFilteredListRequest extends Record<string, unknown> {
  fvg_process_id: string
  cursor: string | null
  limit: number
  verb_filter?: string | null
}
