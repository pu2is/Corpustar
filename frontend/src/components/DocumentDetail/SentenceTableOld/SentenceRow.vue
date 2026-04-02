<script setup lang="ts">
import { computed, ref, toRef, watch } from 'vue'

import LastSentenceOfPrevPage from '@/components/DocumentDetail/SentenceTableOld/LastSentenceOfPrevPage.vue'

import { useSentenceTokenById } from '@/composables/SentenceTableOld/tokenById'
import { useSentenceActions } from '@/composables/SentenceTableOld/actions'
import { usePaginationStore } from '@/stores/local/paginationStore'
import { useSentenceStore } from '@/stores/sentenceStore'
import type { SentenceItem } from '@/types/sentences'

const props = defineProps<{
  sentenceItems: SentenceItem[]
}>()
const sentenceItems = toRef(props, 'sentenceItems')

const sentenceItemPerPage = Number.parseInt(import.meta.env.VITE_SENTENCE_ITEM_PER_PAGE ?? '10', 10)

const sentenceStore = useSentenceStore()
const paginationStore = usePaginationStore()

const scrollAreaRef = ref<HTMLDivElement | null>(null)
const selectedClip = ref<{ sentenceId: string; splitOffset: number } | null>(null)
const lastSentenceItem = ref<SentenceItem | null>(null)
const lastSentenceOnPrevPage = new Map<string, SentenceItem | null>()
let lastSentenceRequestToken = 0

const docId = computed(() => sentenceItems.value[0]?.doc_id ?? '')
const segmentationId = computed(() => sentenceItems.value[0]?.version_id ?? '')
const paginationEntry = computed(() => paginationStore.getPaginationEntry(docId.value, 'sentence'))
const pageLoading = computed(() => paginationEntry.value.loading)
const currentPage = computed(() => paginationEntry.value.currentPage)

const { sentenceTokensById } = useSentenceTokenById(sentenceItems)
const { highlightedSentenceIdSet, mutationLoading, mergePreviousSentence, clipSentence, resetActionState } = useSentenceActions({
  sentenceItems,
  lastSentenceItem,
  scrollAreaRef,
  lastSentenceOnPrevPage,
})
const tableLoading = computed(() => pageLoading.value || mutationLoading.value)
const sentenceActionLoading = computed(() => pageLoading.value || mutationLoading.value)

function isLastToken(sentenceId: string, tokenIndex: number): boolean {
  const sentenceTokens = sentenceTokensById.value.get(sentenceId) ?? []
  return tokenIndex === sentenceTokens.length - 1
}

function canMergePrevious(index: number, item: SentenceItem): boolean {
  return index > 0 || (index === 0 && item.start_offset > 0 && lastSentenceItem.value !== null)
}

function isSelectedSplit(sentenceId: string, splitOffset: number | null): boolean {
  if (splitOffset === null || selectedClip.value === null) {
    return false
  }

  return selectedClip.value.sentenceId === sentenceId && selectedClip.value.splitOffset === splitOffset
}

function toggleSplit(sentenceId: string, splitOffset: number | null, isLast: boolean): void {
  if (splitOffset === null || isLast || tableLoading.value) {
    return
  }

  if (isSelectedSplit(sentenceId, splitOffset)) {
    selectedClip.value = null
    return
  }

  selectedClip.value = { sentenceId, splitOffset }
}

function canClip(sentenceId: string): boolean {
  return selectedClip.value?.sentenceId === sentenceId
}

async function requestMerge(sentenceId: string): Promise<void> {
  selectedClip.value = null
  await mergePreviousSentence(sentenceId)
}

async function requestClip(sentenceId: string): Promise<void> {
  const splitOffset = selectedClip.value?.sentenceId === sentenceId
    ? selectedClip.value.splitOffset
    : null
  if (splitOffset === null || tableLoading.value) {
    return
  }

  selectedClip.value = null
  await clipSentence(sentenceId, splitOffset)
}

async function loadLastSentenceItem(): Promise<void> {
  const currentDocId = docId.value
  const processingId = segmentationId.value
  const firstSentence = sentenceItems.value[0]
  const requestToken = ++lastSentenceRequestToken
  if (!currentDocId || !processingId || !firstSentence
    || firstSentence.start_offset === 0 || currentPage.value <= 1) {
    lastSentenceItem.value = null
    return
  }

  const previousPageOffset = paginationEntry.value.offsets[currentPage.value - 2] ?? null
  const previousPageCursor = typeof previousPageOffset === 'number' ? previousPageOffset : null
  const cacheKey = `${currentDocId}::${processingId}::${previousPageCursor ?? 'null'}`

  if (lastSentenceOnPrevPage.has(cacheKey)) {
    lastSentenceItem.value = lastSentenceOnPrevPage.get(cacheKey) ?? null
    return
  }

  lastSentenceItem.value = null

  try {
    const previousPage = await sentenceStore.getSentences(
      currentDocId,
      processingId,
      previousPageCursor,
      sentenceItemPerPage,
      false,
    )
    if (requestToken !== lastSentenceRequestToken) {
      return
    }

    lastSentenceItem.value = previousPage.items[previousPage.items.length - 1] ?? null
    lastSentenceOnPrevPage.set(cacheKey, lastSentenceItem.value)
  } catch {
    if (requestToken !== lastSentenceRequestToken) {
      return
    }

    lastSentenceItem.value = null
    lastSentenceOnPrevPage.delete(cacheKey)
  }
}

watch(
  [docId, segmentationId],
  () => {
    selectedClip.value = null
    lastSentenceItem.value = null
    resetActionState()
    lastSentenceOnPrevPage.clear()
  },
)

watch(
  [
    docId,
    segmentationId,
    currentPage,
    () => sentenceItems.value[0]?.id ?? '',
    () => sentenceItems.value[0]?.start_offset ?? 0,
  ],
  () => {
    void loadLastSentenceItem()
  },
  { immediate: true },
)

watch(sentenceItems, (items) => {
  if (selectedClip.value === null) {
    return
  }

  if (!items.some((item) => item.id === selectedClip.value?.sentenceId)) {
    selectedClip.value = null
  }
})
</script>

<template>
  <LastSentenceOfPrevPage
    :last-sentence-item="lastSentenceItem" />

  <div ref="scrollAreaRef"
    class="scroll-area min-h-0 flex-1 overflow-y-auto">
    <article v-for="(item, index) in sentenceItems"
      :key="item.id"
      class="mb-2 border p-2 transition-colors duration-200"
      :class="highlightedSentenceIdSet.has(item.id) ? 'border-emerald-500 bg-emerald-50/60' : 'border-border'">
      <p class="text-xs text-text-muted">
        {{ item.start_offset }} - {{ item.end_offset }}
      </p>

      <div class="mt-1 flex flex-wrap gap-1 break-words text-sm">
        <template v-for="(wordToken, wordIndex) in sentenceTokensById.get(item.id) ?? []"
          :key="wordToken.key">
          <button v-if="wordToken.isSymbol"
            type="button"
            :disabled="isLastToken(item.id, wordIndex) || tableLoading"
            class="rounded-none px-1 transition-colors duration-150 disabled:cursor-default"
            :class="[
              isLastToken(item.id, wordIndex)
                ? ''
                : 'cursor-pointer hover:bg-emerald-600 hover:text-emerald-50',
              isSelectedSplit(item.id, wordToken.splitOffset) ? 'bg-emerald-700 text-emerald-50' : '',
            ]"
            @click="toggleSplit(item.id, wordToken.splitOffset, isLastToken(item.id, wordIndex))">
            {{ wordToken.value }}
          </button>
          <span v-else
            class="rounded-none px-1 transition-colors duration-150"
            :class="isLastToken(item.id, wordIndex) ? '' : 'hover:bg-sky-600 hover:text-sky-100'">
            {{ wordToken.value }}
          </span>
        </template>
      </div>

      <div class="mt-2 flex gap-2">
        <button type="button"
          :disabled="sentenceActionLoading || !canMergePrevious(index, item)"
          class="cursor-pointer bg-violet-200 px-3 py-0.5 text-xs text-violet-700 disabled:cursor-not-allowed disabled:opacity-60"
          @click="void requestMerge(item.id)">
          Merge Prev
        </button>
        <button type="button"
          :disabled="sentenceActionLoading || !canClip(item.id)"
          class="cursor-pointer bg-fuchsia-100 px-3 py-0.5 text-xs text-fuchsia-700 disabled:cursor-not-allowed disabled:bg-gray-200 disabled:text-gray-600 disabled:opacity-60"
          @click="void requestClip(item.id)">
          Clip
        </button>
      </div>
    </article>
  </div>
</template>
