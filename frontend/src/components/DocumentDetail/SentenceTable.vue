<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

import LastSentenceOfPrevPage from '@/components/DocumentDetail/SentenceTable/LastSentenceOfPrevPage.vue'

import { useProcessStore } from '@/stores/processStore'
import { useSentenceStore } from '@/stores/sentenceStore'
import type { SentenceItem } from '@/types/sentences'
import { usePaginationStore } from '@/stores/local/paginationStore'

const props = defineProps<{
  docId: string
}>()

interface SentenceWordToken {
  key: string
  value: string
  isSymbol: boolean
  splitOffset: number | null
}

const sentenceItemPerPage = Number.parseInt(import.meta.env.VITE_SENTENCE_ITEM_PER_PAGE ?? '10', 10)

const paginationStore = usePaginationStore()
const processStore = useProcessStore()
const sentenceStore = useSentenceStore()

const scrollAreaRef = ref<HTMLDivElement | null>(null)
const selectedClip = ref<{ sentenceId: string; splitOffset: number } | null>(null)
const highlightedSentenceIds = ref<string[]>([])
const lastSentenceItem = ref<SentenceItem | null>(null)
const lastSentenceLoading = ref(false)
const mutationLoading = ref(false)
const pendingScrollTop = ref<number | null>(null)
const previousPageLastSentenceCache = new Map<string, SentenceItem | null>()
let lastSentenceRequestToken = 0

const activeProcessing = computed(() => processStore.getSentenceSegmentationProcessByDocId(props.docId))
const activeProcessingId = computed(() => activeProcessing.value?.id ?? '')
const activeDocProcessKey = computed(() => (
  props.docId && activeProcessingId.value ? `${props.docId}::${activeProcessingId.value}` : ''
))
const segmentationState = computed(() => (
  processStore
    .getProcessByDocId(props.docId)
    .find((process) => process.type === 'sentence_segmentation')?.state ?? null
))

const paginationEntry = computed(() => paginationStore.getPaginationEntry(props.docId, 'sentence'))
const paginationReady = computed(() => paginationEntry.value.processingId === activeProcessingId.value)
const pageLoading = computed(() => paginationEntry.value.loading)
const currentPage = computed(() => paginationEntry.value.currentPage)
const hasPreviousPage = computed(() => currentPage.value > 1)
const hasNextPage = computed(() => paginationEntry.value.hasMore)
const tableLoading = computed(() => pageLoading.value || mutationLoading.value)
const sentenceActionLoading = computed(() => pageLoading.value || mutationLoading.value)

const sentenceItemIds = computed(() => paginationEntry.value.pageItemIds)
const storedSentenceMap = computed(() => {
  if (!props.docId || !activeProcessingId.value) {
    return new Map<string, SentenceItem>()
  }

  return new Map<string, SentenceItem>(
    sentenceStore
      .getSentenceItems(props.docId, activeProcessingId.value)
      .map((item) => [item.id, item]),
  )
})
const sentenceItems = computed(() => {
  if (!props.docId || !activeProcessingId.value) {
    return []
  }

  if (sentenceItemIds.value.length === 0) {
    return Array.from(storedSentenceMap.value.values())
  }

  return sentenceItemIds.value
    .map((itemId) => storedSentenceMap.value.get(itemId))
    .filter((item): item is SentenceItem => item !== undefined)
})

const showSegmentationLoading = computed(() => (
  segmentationState.value === 'running'
  || (Boolean(activeProcessingId.value) && (!paginationReady.value || (pageLoading.value && sentenceItems.value.length === 0)))
))

const highlightedSentenceIdSet = computed(() => new Set(highlightedSentenceIds.value))
const sentenceTokensById = computed(() => new Map<string, SentenceWordToken[]>(
  sentenceItems.value.map((item) => [item.id, splitSentenceToWords(item)]),
))

function splitSentenceToWords(item: SentenceItem): SentenceWordToken[] {
  const tokenPattern = /[\p{P}\p{S}]|[^\s\p{P}\p{S}]+/gu
  return Array.from(item.source_text.matchAll(tokenPattern), (match, index) => {
    const value = match[0]
    const isSymbol = /^[\p{P}\p{S}]+$/u.test(value)
    return {
      key: `${item.id}-${index}`,
      value,
      isSymbol,
      splitOffset: isSymbol ? item.start_offset + (match.index ?? 0) + 1 : null,
    }
  })
}

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

function setHighlightedSentenceIds(sentenceIds: string[]): void {
  highlightedSentenceIds.value = Array.from(new Set(sentenceIds.filter(Boolean)))
}

function captureScrollPosition(): void {
  const scrollArea = scrollAreaRef.value
  pendingScrollTop.value = scrollArea && scrollArea.scrollHeight > scrollArea.clientHeight
    ? scrollArea.scrollTop
    : null
}

async function restoreScrollPosition(): Promise<void> {
  const scrollTop = pendingScrollTop.value
  if (scrollTop === null) {
    return
  }

  pendingScrollTop.value = null
  await nextTick()
  if (scrollAreaRef.value) {
    scrollAreaRef.value.scrollTop = scrollTop
  }
}

function getPreviousSentenceId(sentenceId: string): string | null {
  const sentenceIndex = sentenceItems.value.findIndex((item) => item.id === sentenceId)

  if (sentenceIndex < 0) {
    return null
  }

  if (sentenceIndex > 0) {
    return sentenceItems.value[sentenceIndex - 1]?.id ?? null
  }

  return sentenceItems.value[0]?.start_offset === 0 ? null : lastSentenceItem.value?.id ?? null
}

async function loadLastSentenceItem(): Promise<void> {
  const currentDocId = props.docId
  const processingId = activeProcessingId.value
  const firstSentence = sentenceItems.value[0]
  const requestToken = ++lastSentenceRequestToken
  if (!currentDocId || !processingId || !firstSentence
    || firstSentence.start_offset === 0 || currentPage.value <= 1) {
    lastSentenceItem.value = null
    lastSentenceLoading.value = false
    return
  }

  const previousPageOffset = paginationEntry.value.offsets[currentPage.value - 2] ?? null
  const previousPageCursor = typeof previousPageOffset === 'number' ? previousPageOffset : null
  const cacheKey = `${currentDocId}::${processingId}::${previousPageCursor ?? 'null'}`
  if (previousPageLastSentenceCache.has(cacheKey)) {
    lastSentenceItem.value = previousPageLastSentenceCache.get(cacheKey) ?? null
    lastSentenceLoading.value = false
    return
  }

  lastSentenceLoading.value = true
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
    previousPageLastSentenceCache.set(cacheKey, lastSentenceItem.value)
  } catch {
    if (requestToken !== lastSentenceRequestToken) {
      return
    }

    lastSentenceItem.value = null
    previousPageLastSentenceCache.delete(cacheKey)
  } finally {
    if (requestToken === lastSentenceRequestToken) {
      lastSentenceLoading.value = false
    }
  }
}

async function goToPreviousPage(): Promise<void> {
  const processingId = activeProcessingId.value
  if (!props.docId || !processingId || !hasPreviousPage.value || tableLoading.value) {
    return
  }

  setHighlightedSentenceIds([])
  await paginationStore.goToPreviousPage(props.docId, processingId, 'sentence')
}

async function goToNextPage(): Promise<void> {
  const processingId = activeProcessingId.value
  if (!props.docId || !processingId || !hasNextPage.value || tableLoading.value) {
    return
  }

  setHighlightedSentenceIds([])
  await paginationStore.goToNextPage(props.docId, processingId, 'sentence')
}

async function mergePreviousSentence(sentenceId: string): Promise<void> {
  const previousSentenceId = getPreviousSentenceId(sentenceId)
  const processingId = activeProcessingId.value
  if (!previousSentenceId || !props.docId || !processingId) {
    return
  }

  captureScrollPosition()
  mutationLoading.value = true
  try {
    const mergedItem = await sentenceStore.mergeSentences([previousSentenceId, sentenceId])
    setHighlightedSentenceIds([mergedItem.id])
    previousPageLastSentenceCache.clear()
    await paginationStore.refreshCurrentPage(props.docId, processingId, 'sentence')
    await restoreScrollPosition()
  } catch {
    pendingScrollTop.value = null
  } finally {
    mutationLoading.value = false
  }
}

async function clipSentence(sentenceId: string, splitOffset: number): Promise<void> {
  const processingId = activeProcessingId.value
  if (!props.docId || !processingId) {
    return
  }

  captureScrollPosition()
  mutationLoading.value = true
  try {
    await sentenceStore.clipSentence(sentenceId, splitOffset)
    setHighlightedSentenceIds([])
    previousPageLastSentenceCache.clear()
    await paginationStore.refreshCurrentPage(props.docId, processingId, 'sentence')
    await restoreScrollPosition()
  } catch {
    pendingScrollTop.value = null
  } finally {
    mutationLoading.value = false
  }
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

watch(
  activeDocProcessKey,
  async (nextKey) => {
    highlightedSentenceIds.value = []
    selectedClip.value = null
    lastSentenceItem.value = null
    lastSentenceLoading.value = false
    pendingScrollTop.value = null
    previousPageLastSentenceCache.clear()

    if (!nextKey || !props.docId || !activeProcessingId.value) {
      return
    }

    await paginationStore.initializeDocumentPagination(props.docId, activeProcessingId.value, 'sentence')
  },
  { immediate: true },
)

watch(
  [
    activeDocProcessKey,
    currentPage,
    () => sentenceItems.value[0]?.id ?? '',
    () => sentenceItems.value[0]?.start_offset ?? 0,
  ],
  () => {
    void loadLastSentenceItem()
  },
  { immediate: true },
)

watch([activeProcessingId, currentPage], () => {
  selectedClip.value = null
})

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
  <section class="min-h-0 flex flex-1 flex-col overflow-hidden bg-background-elevated/15">
    <p v-if="showSegmentationLoading"
      class="p-3 text-sm text-text-muted">
      Loading sentences...
    </p>
    <p v-else-if="sentenceItems.length === 0"
      class="p-3 text-sm text-text-muted">
      No sentences in this segmentation result.
    </p>

    <template v-else>
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
              <span
                v-else
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

      <footer class="bg-violet-200/60 px-4 py-3 text-violet-950 shadow-[0_16px_36px_-24px_rgba(109,40,217,0.9)] backdrop-blur-md">
        <div class="flex items-center justify-between gap-3">
          <p class="text-sm font-medium">
            Page {{ currentPage }}
          </p>
          <div class="flex items-center gap-2">
            <button
              type="button"
              :disabled="tableLoading || !hasPreviousPage"
              class="cursor-pointer bg-white/45 px-3 py-1.5 text-xs font-semibold text-violet-900 transition hover:bg-white/70 disabled:cursor-not-allowed disabled:opacity-45"
              @click="void goToPreviousPage()">
              Prev
            </button>
            <button
              type="button"
              :disabled="tableLoading || !hasNextPage"
              class="cursor-pointer bg-violet-500 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-violet-600/85 disabled:cursor-not-allowed disabled:opacity-45"
              @click="void goToNextPage()">
              Next
            </button>
          </div>
        </div>
      </footer>
    </template>
  </section>
</template>
