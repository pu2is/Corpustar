<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
// components
import LastSentenceItem from '@/components/DocumentDetail/Content/LastSentenceItem.vue'
import SentencePagination from '@/components/DocumentDetail/Content/SentencePagination.vue'
import SentencesOfDocument from '@/components/DocumentDetail/Content/SentenceSegmentation/SentencesOfDocument.vue'
// store
import { useLemmaStore } from '@/stores/lemmaStore'
import { usePaginationStore } from '@/stores/local/paginationStore'
import { useProcessStore } from '@/stores/processStore'
import { useSentenceStore } from '@/stores/sentenceStore'
import type { LemmaItem } from '@/types/lemmas'
import type { SentenceItem } from '@/types/sentences'

const route = useRoute()
const lemmaStore = useLemmaStore()
const paginationStore = usePaginationStore()
const processStore = useProcessStore()
const sentenceStore = useSentenceStore()

const docId = computed(() => {
  const value = route.params.doc_id
  return typeof value === 'string' ? value : ''
})
const activeProcessing = computed(() => processStore.getSentenceSegmentationProcessByDocId(docId.value))
const activeProcessingId = computed(() => activeProcessing.value?.id ?? '')
const activeLemmatizeProcess = computed(() => processStore.getLemmatizeProcessBySegmentationId(
  docId.value,
  activeProcessingId.value,
))
const activeDocProcessKey = computed(() => (
  docId.value && activeProcessingId.value ? `${docId.value}::${activeProcessingId.value}` : ''
))
const displayType = computed(() => sentenceStore.displayType ?? 'source')
const showLemma = computed(() => displayType.value === 'lemma')
const sentenceEditingLocked = computed(() => (
  activeLemmatizeProcess.value?.state === 'running' || activeLemmatizeProcess.value?.state === 'succeed'
))

// -------------------- //
// Fetch Sentence Items //
// -------------------- //
const sentenceItemPerPage = Number.parseInt(import.meta.env.VITE_SENTENCE_ITEM_PER_PAGE ?? '10', 10)
const lastSentenceItem = ref<SentenceItem | null>(null)
const lastSentenceLoading = ref(false)
let lastSentenceRequestToken = 0

const sentenceItems = computed(() => {
  if (!docId.value || !activeProcessingId.value) {
    return []
  }

  return sentenceStore.getSentenceItems(docId.value, activeProcessingId.value)
})
const storedLemmaBySentenceId = computed(() => new Map<string, LemmaItem>(
  lemmaStore
    .getLemmasBySegmentationId(activeProcessingId.value)
    .map((lemma) => [lemma.sentenceId, lemma]),
))
const displayItems = computed(() => {
  if (!showLemma.value) {
    return sentenceItems.value
  }

  return sentenceItems.value
    .map((sentence) => {
      const lemma = storedLemmaBySentenceId.value.get(sentence.id)
      if (!lemma) {
        return null
      }

      return {
        ...sentence,
        text: lemma.correctedLemma,
      }
    })
    .filter((item): item is SentenceItem => item !== null)
})
const lemmaLoading = ref(false)
let lemmaRequestToken = 0

const lemmaPageReady = computed(() => (
  sentenceItems.value.length > 0
  && sentenceItems.value.every((sentence) => storedLemmaBySentenceId.value.has(sentence.id))
))

async function loadLastSentenceItem(): Promise<void> {
  const currentDocId = docId.value
  const processingId = activeProcessingId.value
  const firstSentence = sentenceItems.value[0]
  const requestToken = ++lastSentenceRequestToken
  if (!currentDocId || !processingId || !firstSentence
    || firstSentence.startOffset === 0 || currentPage.value <= 1) {
    lastSentenceItem.value = null
    lastSentenceLoading.value = false
    return
  }

  const previousPageOffset = paginationEntry.value.offsets[currentPage.value - 2] ?? null
  lastSentenceLoading.value = true
  lastSentenceItem.value = null

  try {
    const previousPage = await sentenceStore.getSentences(
      currentDocId,
      processingId,
      previousPageOffset,
      sentenceItemPerPage,
      false,
    )
    if (requestToken !== lastSentenceRequestToken) {
      return
    }

    lastSentenceItem.value = previousPage.items[previousPage.items.length - 1] ?? null
  } catch {
    if (requestToken !== lastSentenceRequestToken) {
      return
    }

    lastSentenceItem.value = null
  } finally {
    if (requestToken === lastSentenceRequestToken) {
      lastSentenceLoading.value = false
    }
  }
}


// ---------- //
// Pagination //
// ---------- //
const paginationEntry = computed(() => paginationStore.getPaginationEntry(docId.value))
const pageLoading = computed(() => paginationEntry.value.loading)
const currentPage = computed(() => paginationEntry.value.currentPage)
const hasPreviousPage = computed(() => currentPage.value > 1)
const hasNextPage = computed(() => paginationEntry.value.hasMore)
const tableLoading = computed(() => pageLoading.value || mutationLoading.value || (showLemma.value && lemmaLoading.value))

async function goToPreviousPage(): Promise<void> {
  const currentDocId = docId.value
  const processingId = activeProcessingId.value
  if (!currentDocId || !processingId || !hasPreviousPage.value || tableLoading.value) {
    return
  }

  setHighlightedSentenceIds([])
  await paginationStore.goToPreviousPage(currentDocId, processingId)
}

async function goToNextPage(): Promise<void> {
  const currentDocId = docId.value
  const processingId = activeProcessingId.value
  if (!currentDocId || !processingId || !hasNextPage.value || tableLoading.value) {
    return
  }

  setHighlightedSentenceIds([])
  await paginationStore.goToNextPage(currentDocId, processingId)
}


// ------------ //
// Merge & Clip //
// ------------ //
const mutationLoading = ref(false)
const scrollAreaRef = ref<HTMLDivElement | null>(null)
const pendingScrollTop = ref<number | null>(null)

const sentenceActionLoading = computed(() => pageLoading.value || mutationLoading.value)

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
  const items = sentenceItems.value
  const sentenceIndex = items.findIndex((item) => item.id === sentenceId)

  if (sentenceIndex < 0) { return null }

  if (sentenceIndex > 0) { return items[sentenceIndex - 1]?.id ?? null }

  return items[0]?.startOffset === 0 ? null : lastSentenceItem.value?.id ?? null
}

async function mergePreviousSentence(sentenceId: string): Promise<void> {
  const previousSentenceId = getPreviousSentenceId(sentenceId)
  const currentDocId = docId.value
  const processingId = activeProcessingId.value
  if (!previousSentenceId || !currentDocId || !processingId || sentenceEditingLocked.value) {
    return
  }

  captureScrollPosition()
  mutationLoading.value = true
  try {
    const mergedItem = await sentenceStore.mergeSentences([previousSentenceId, sentenceId])
    setHighlightedSentenceIds([mergedItem.id])
    await paginationStore.refreshCurrentPage(currentDocId, processingId)
    await restoreScrollPosition()
  } catch {
    pendingScrollTop.value = null
  } finally {
    mutationLoading.value = false
  }
}

async function clipSentence(sentenceId: string, splitOffset: number): Promise<void> {
  const currentDocId = docId.value
  const processingId = activeProcessingId.value
  if (!currentDocId || !processingId || sentenceEditingLocked.value) {
    return
  }

  mutationLoading.value = true
  captureScrollPosition()
  try {
    const clippedItems = await sentenceStore.clipSentence(sentenceId, splitOffset)
    setHighlightedSentenceIds(clippedItems.slice(0, 2).map((item) => item.id))
    await paginationStore.refreshCurrentPage(currentDocId, processingId)
    await restoreScrollPosition()
  } catch {
    pendingScrollTop.value = null
  } finally {
    mutationLoading.value = false
  }
}

// --------- //
// Highlight //
// --------- //
const highlightedSentenceIds = ref<string[]>([])

const highlightedSentenceIdSet = computed(() => new Set(highlightedSentenceIds.value))

function setHighlightedSentenceIds(sentenceIds: string[]): void {
  highlightedSentenceIds.value = Array.from(new Set(sentenceIds.filter(Boolean)))
}

async function loadLemmaPage(): Promise<void> {
  const processingId = activeProcessingId.value
  const requestToken = ++lemmaRequestToken
  if (!showLemma.value || !processingId || activeLemmatizeProcess.value?.state !== 'succeed' || sentenceItems.value.length === 0) {
    lemmaLoading.value = false
    return
  }

  const firstSentence = sentenceItems.value[0]
  if (!firstSentence) {
    lemmaLoading.value = false
    return
  }

  if (firstSentence.startOffset > 0 && (lastSentenceLoading.value || !lastSentenceItem.value?.lemmaText)) {
    return
  }

  lemmaLoading.value = true
  try {
    const startFromId = firstSentence.startOffset === 0 ? null : (lastSentenceItem.value?.lemmaText ?? null)
    await lemmaStore.getLemmaItems(processingId, startFromId, sentenceItems.value.length)
  } finally {
    if (requestToken === lemmaRequestToken) {
      lemmaLoading.value = false
    }
  }
}

watch(
  activeDocProcessKey,
  async (nextKey) => {
    highlightedSentenceIds.value = []
    lastSentenceItem.value = null
    lastSentenceLoading.value = false
    lemmaLoading.value = false
    pendingScrollTop.value = null
    if (!nextKey || !docId.value || !activeProcessingId.value) {
      return
    }

    await paginationStore.initializeDocumentPagination(docId.value, activeProcessingId.value)
  },
  { immediate: true },
)

watch(
  [
    activeDocProcessKey,
    currentPage,
    () => sentenceItems.value[0]?.id ?? '',
    () => sentenceItems.value[0]?.startOffset ?? 0,
  ],
  () => {
    void loadLastSentenceItem()
  },
  { immediate: true },
)

watch(
  [
    showLemma,
    activeDocProcessKey,
    () => activeLemmatizeProcess.value?.state ?? '',
    () => sentenceItems.value.map((item) => item.id).join('|'),
    () => lastSentenceItem.value?.lemmaText ?? '',
    () => lastSentenceLoading.value,
  ],
  () => {
    void loadLemmaPage()
  },
  { immediate: true },
)

watch(
  () => activeLemmatizeProcess.value?.state ?? '',
  (state) => {
    if (state !== 'succeed' || !docId.value || !activeProcessingId.value) {
      return
    }

    void paginationStore.refreshCurrentPage(docId.value, activeProcessingId.value)
  },
)
</script>

<template>
  <div class="min-h-0 flex flex-1 flex-col gap-3 overflow-hidden">
    <p v-if="pageLoading && sentenceItems.length === 0"
      class="text-sm text-text-muted">
      Loading sentences...
    </p>

    <p v-else-if="sentenceItems.length === 0"
      class="text-sm text-text-muted">
      No sentences in this segmentation result.
    </p>

    <p v-else-if="showLemma && !lemmaPageReady && lemmaLoading"
      class="text-sm text-text-muted">
      Loading lemmas...
    </p>

    <p v-else-if="showLemma && displayItems.length === 0"
      class="text-sm text-text-muted">
      No lemmas available for this page.
    </p>

    <div v-else class="min-h-0 flex flex-1 flex-col overflow-hidden bg-background-elevated/15">
      <div ref="scrollAreaRef" class="scroll-area min-h-0 flex-1 overflow-y-auto">
        <LastSentenceItem v-if="!showLemma" :item="lastSentenceItem"
          :loading="sentenceActionLoading || lastSentenceLoading" />

        <div class="space-y-2">
          <SentencesOfDocument v-for="(item, index) in displayItems"
            :key="item.id" :item="item" :loading="tableLoading"
            :can-merge-prev="!showLemma && (index > 0 || (index === 0 && item.startOffset > 0 && lastSentenceItem !== null))"
            :highlighted="highlightedSentenceIdSet.has(item.id)"
            :allow-sentence-actions="!showLemma && !sentenceEditingLocked"
            @request-merge="mergePreviousSentence" @clip="clipSentence" />
        </div>
      </div>

      <SentencePagination :current-page="currentPage" :item-count="displayItems.length"
        :has-previous="hasPreviousPage" :has-next="hasNextPage" :loading="tableLoading"
        @previous="goToPreviousPage" @next="goToNextPage" />
    </div>
  </div>
</template>
