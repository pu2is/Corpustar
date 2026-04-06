<script setup lang="ts">
import { computed, ref } from 'vue'
import { useFvgCandidateStore } from '@/stores/fvgCandidate'

import type { SentenceFvgItem } from '@/types/fvg'
import FvgCandidateBadge from './FvgCandidateBadge.vue'
import Lemmas from './Lemmas.vue'

const fvgCandidateStore = useFvgCandidateStore()
const sentenceList = computed(() => fvgCandidateStore.sentenceFvgList)

// Tokens
interface TokenItem {
  text: string
  lemma: string
}

function sentenceToTokens(sentence: string): string[] {
  if (sentence.length === 0) return []
  const tokenPattern = /[\p{P}\p{S}]|[^\s\p{P}\p{S}]+/gu
  return Array.from(sentence.matchAll(tokenPattern), (match) => match[0])
}

const tokens = computed(() => new Map(
  sentenceList.value.map((item) => {
    const lemmaByIndex = new Map(item.lemma_tokens.map((l) => [l.word_index, l.lemma_word]))
    return [ item.id,
      sentenceToTokens(item.corrected_text || item.source_text).map((text, i): TokenItem => ({
        text,
        lemma: lemmaByIndex.get(i) ?? '',
      })),
    ]
  }),
))

function candidateTokenIndices(item: SentenceFvgItem): Set<number> {
  const indices = new Set<number>()
  for (const c of item.fvg_candidates) {
    if (c.removed) continue
    if (c.algo_verb_index >= 0) indices.add(c.algo_verb_index)
    if (c.algo_noun_index >= 0) indices.add(c.algo_noun_index)
    if (c.algo_prep_index >= 0) indices.add(c.algo_prep_index)
  }
  return indices
}

function removedCandidateTokenIndices(item: SentenceFvgItem): Set<number> {
  const indices = new Set<number>()
  for (const c of item.fvg_candidates) {
    if (!c.removed) continue
    if (c.algo_verb_index >= 0) indices.add(c.algo_verb_index)
    if (c.algo_noun_index >= 0) indices.add(c.algo_noun_index)
    if (c.algo_prep_index >= 0) indices.add(c.algo_prep_index)
  }
  return indices
}

// hover lemma highlight source text
const hoveredLemmaIndex = ref<Record<string, number | null>>({})

function onLemmaHover(sentenceId: string, wordIndex: number | null): void {
  hoveredLemmaIndex.value[sentenceId] = wordIndex
}

function tokenClass(item: SentenceFvgItem, tokenIndex: number): string {
  if (candidateTokenIndices(item).has(tokenIndex))
    return 'px-1 bg-yellow-300 text-violet-700 font-medium'
  if (removedCandidateTokenIndices(item).has(tokenIndex))
    return 'px-1'
  if (hoveredLemmaIndex.value[item.id] === tokenIndex)
    return 'px-1 bg-violet-100 text-violet-700 font-medium'
  return 'px-1 text-contrast-strong'
}
</script>

<template>
  <article v-for="item in sentenceList"
    :key="item.id"
    class="mb-2 border border-border p-2 space-y-2">
    <p class="text-xs text-text-muted">
      <span class="font-medium small-caps">Span</span> {{ item.start_offset }} – {{ item.end_offset }}
    </p>
    <div v-if="item.fvg_candidates.length > 0" class="flex flex-wrap gap-1">
      <FvgCandidateBadge v-for="candidate in item.fvg_candidates"
        :key="candidate.id" 
        :sentence-id="item.id" :fvg-candidate-item="candidate" />
    </div>

    <div class="cursor-default flex flex-wrap gap-1 text-sm">
      <span v-for="(token, tokenIndex) in tokens.get(item.id) ?? []"
        :key="`${item.id}-${tokenIndex}`"
        :title="token.lemma || undefined"
        :class="tokenClass(item, tokenIndex)">
        {{ token.text }}
      </span>
    </div>

    <Lemmas v-if="item.fvg_candidates.length === 0 && item.lemma_tokens.length > 0"
      :lemma-tokens="item.lemma_tokens"
      @hover-lemma="(idx) => onLemmaHover(item.id, idx)" />

  </article>
</template>