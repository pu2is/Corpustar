<script setup lang="ts">
import { computed } from 'vue'
import { useFvgCandidateStore } from '@/stores/fvgCandidate'
import type { SentenceFvgItem } from '@/types/fvg'

const fvgCandidateStore = useFvgCandidateStore()
const sentenceList = computed(() => fvgCandidateStore.sentenceFvgList)

// Tokens
interface TokenItem {
  text: string
  isSymbol: boolean
}

function sentenceToTokens(sentence: string): TokenItem[] {
  if (sentence.length === 0) return []
  const tokenPattern = /[\p{P}\p{S}]|[^\s\p{P}\p{S}]+/gu
  return Array.from(sentence.matchAll(tokenPattern), (match) => ({
    text: match[0],
    isSymbol: /^[\p{P}\p{S}]+$/u.test(match[0]),
  }))
}

const tokens = computed(() => new Map(
  sentenceList.value.map((item) => [
    item.id,
    sentenceToTokens(item.corrected_text || item.source_text),
  ]),
))

function candidateTokenIndices(item: SentenceFvgItem): Set<number> {
  const indices = new Set<number>()
  for (const c of item.fvg_candidates) {
    if (c.algo_verb_index >= 0) indices.add(c.algo_verb_index)
    if (c.algo_noun_index >= 0) indices.add(c.algo_noun_index)
    if (c.algo_prep_index >= 0) indices.add(c.algo_prep_index)
  }
  return indices
}
</script>

<template>
  <article v-for="item in sentenceList"
    :key="item.id"
    class="mb-2 border border-border p-2">
    <p class="mb-1.5 text-xs text-muted">
      {{ item.start_offset }} – {{ item.end_offset }}
    </p>

    <div class="flex flex-wrap gap-1 text-sm">
      <span
        v-for="(token, tokenIndex) in tokens.get(item.id) ?? []"
        :key="`${item.id}-${tokenIndex}`"
        :class="[
          token.isSymbol ? 'px-0.5' : 'px-1',
          candidateTokenIndices(item).has(tokenIndex)
            ? 'bg-violet-100 text-violet-700 font-medium'
            : 'text-contrast-strong',
        ]">
        {{ token.text }}
      </span>
    </div>

    <div v-if="item.fvg_candidates.length > 0" class="mt-2 flex flex-wrap gap-1.5">
      <span
        v-for="candidate in item.fvg_candidates"
        :key="candidate.id"
        class="inline-flex items-center gap-1 border border-violet-200 bg-violet-50 px-2 py-0.5 text-xs text-violet-700">
        {{ candidate.algo_verb_token }}
        <span class="text-violet-300">·</span>
        {{ candidate.algo_noun_token }}
        <template v-if="candidate.algo_prep_token">
          <span class="text-violet-300">·</span>
          {{ candidate.algo_prep_token }}
        </template>
      </span>
    </div>
  </article>
</template>