<script setup lang="ts">
import { computed, ref, watch } from 'vue'
// icons
import { CirclePlus, Plus } from 'lucide-vue-next'
// stores
import { useFvgCandidateStore } from '@/stores/fvgCandidate'
import { useProcessStore } from '@/stores/processStore'
// composables
import { getIdFromUrl } from '@/composables/useRouteId'
// types
import type { SentenceFvgItem } from '@/types/fvg'
import type { LemmaItem } from '@/types/lemmatize'
// components
import FvgCandidateBadge from '@/components/DocumentDetail/FvgSentenceTable/FvgCandidateBadge.vue'
import SentenceLemmaBadges from '@/components/DocumentDetail/FvgSentenceTable/SentenceLemmaBadges.vue'
import AddUndetectedFvg from '@/components/DocumentDetail/FvgSentenceTable/AddUndetectedFvg.vue'

const docId = getIdFromUrl()
const fvgCandidateStore = useFvgCandidateStore()
const processStore = useProcessStore()

const sentenceList = computed(() => fvgCandidateStore.sentenceFvgList)
const segmentationId = computed(() => sentenceList.value[0]?.version_id ?? '')
const ruleId = computed(() => processStore.getRuleIdBySegmentationId(segmentationId.value ?? ''))
const fvgProcessId = computed(() => processStore.getFvgProcessByDocId(docId.value)?.id ?? null)


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

// toggle lemma badges visibility per sentence (hidden by default when candidates exist)
const showLemmas = ref<Record<string, boolean>>({})

// hover lemma highlight source text
const hoveredLemmaIndex = ref<Record<string, number | null>>({})
const chosenLemmaIndices = ref<Record<string, Set<number>>>({})
const chosenLemmaItems = ref<Record<string, LemmaItem[]>>({})
const activePinnedSentenceId = ref<string | null>(null)
// choosing
const activeChoosingId = ref<string | null>(null)
const clearSignals = ref<Record<string, number>>({})
const modalOpen = ref(false)

const activePair = computed((): { verb: LemmaItem; noun: LemmaItem; adp?: LemmaItem } | null => {
  if (!activeChoosingId.value) return null
  const items = chosenLemmaItems.value[activeChoosingId.value] ?? []
  if (items.length < 2) return null
  const verbs = items.filter((l) => l.pos_tag === 'VERB' || l.pos_tag === 'AUX')
  const nouns = items.filter((l) => l.pos_tag === 'NOUN')
  const adps  = items.filter((l) => l.pos_tag === 'ADP')
  if (verbs.length !== 1 || nouns.length !== 1 || adps.length > 1) return null
  return { verb: verbs[0]!, noun: nouns[0]!, ...(adps[0] ? { adp: adps[0] } : {}) }
})

watch(activePair, (pair) => { if (!pair) modalOpen.value = false })

function onLemmaHover(sentenceId: string, wordIndex: number | null): void {
  hoveredLemmaIndex.value[sentenceId] = wordIndex
}

function onChosenIndices(sentenceId: string, wordIndices: number[], lemmaTokens: LemmaItem[]): void {
  // Clear previous sentence when switching
  if (wordIndices.length > 0 && activeChoosingId.value !== null && activeChoosingId.value !== sentenceId) {
    clearSignals.value[activeChoosingId.value] = (clearSignals.value[activeChoosingId.value] ?? 0) + 1
    chosenLemmaIndices.value[activeChoosingId.value] = new Set()
    chosenLemmaItems.value[activeChoosingId.value] = []
  }
  if (wordIndices.length > 0) activeChoosingId.value = sentenceId
  else if (activeChoosingId.value === sentenceId) activeChoosingId.value = null
  const indexSet = new Set(wordIndices)
  chosenLemmaIndices.value[sentenceId] = indexSet
  chosenLemmaItems.value[sentenceId] = lemmaTokens.filter((l) => indexSet.has(l.word_index))
}

function toggleShowLemma(item: SentenceFvgItem): void {
  const isShowing = showLemmas.value[item.id]
  showLemmas.value[item.id] = !isShowing
  if (isShowing) {
    chosenLemmaIndices.value[item.id] = new Set()
    chosenLemmaItems.value[item.id] = []
    hoveredLemmaIndex.value[item.id] = null
    clearSignals.value[item.id] = (clearSignals.value[item.id] ?? 0) + 1
    if (activeChoosingId.value === item.id) activeChoosingId.value = null
  }
}

function tokenClass(item: SentenceFvgItem, tokenIndex: number): string {
  if (candidateTokenIndices(item).has(tokenIndex))
    return 'px-1 bg-yellow-300 text-violet-700 font-medium'
  if (removedCandidateTokenIndices(item).has(tokenIndex))
    return 'px-1'
  if (chosenLemmaIndices.value[item.id]?.has(tokenIndex))
    return 'px-1 bg-green-100 text-green-800 font-medium'
  if (hoveredLemmaIndex.value[item.id] === tokenIndex)
    return 'px-1 bg-violet-100 text-violet-700 font-medium'
  return 'px-1 text-contrast-strong'
}
</script>

<template>
  <article v-for="item in sentenceList"
    :key="item.id"
    class="relative mb-2 border border-border p-2 space-y-2">
    <p class="text-xs text-text-muted">
      <span class="font-medium small-caps">Span</span> {{ item.start_offset }} – {{ item.end_offset }}
    </p>

    <div v-if="item.fvg_candidates.length > 0" class="flex flex-wrap gap-1 items-center">
      <FvgCandidateBadge v-for="candidate in item.fvg_candidates"
        :key="candidate.id"
        :sentence-id="item.id" :fvg-candidate-item="candidate" />
      <button v-if="item.lemma_tokens.length > 0"
        class="cursor-pointer inline-flex items-center justify-center w-5 h-5 bg-gray-300/50 text-gray-400 hover:border-gray-400 hover:text-gray-600 transition-colors"
        :title="showLemmas[item.id] ? 'Hide lemma badges' : 'Show lemma badges'"
        @click="toggleShowLemma(item)">
        <Plus :size="10" />
      </button>
    </div>

    <div class="cursor-default flex flex-wrap gap-1 text-sm">
      <span v-for="lemmaToken in item.lemma_tokens"
        :key="`${item.id}-${lemmaToken.word_index}`"
        :title="lemmaToken.lemma_word || undefined"
        :class="tokenClass(item, lemmaToken.word_index)">
        {{ lemmaToken.source_word }}
      </span>
    </div>

    <SentenceLemmaBadges v-if="item.lemma_tokens.length > 0 && (item.fvg_candidates.length === 0 || showLemmas[item.id])"
      :lemma-tokens="item.lemma_tokens"
      :is-active="activePinnedSentenceId === null || activePinnedSentenceId === item.id"
      :clear-signal="clearSignals[item.id]"
      @pinned="activePinnedSentenceId = item.id"
      @hover-lemma="(idx) => onLemmaHover(item.id, idx)"
      @chosen-indices="(indices) => onChosenIndices(item.id, indices, item.lemma_tokens)" />

    <div v-if="item.id === activeChoosingId && activePair"
      class="absolute right-0 top-0 bottom-0 flex items-center">
      <button class="h-full px-2 flex items-center justify-center 
        bg-violet-400/40 text-violet-700 hover:bg-violet-500/50 transition-colors"
        @click="modalOpen = true">
        <CirclePlus :size="13" />
      </button>
    </div>
  </article>

  <AddUndetectedFvg :pair="activePair" :is-open="modalOpen" :rule-id="ruleId"
    :sentence-id="activeChoosingId" :process-id="fvgProcessId"
    @close="modalOpen = false" />
</template>