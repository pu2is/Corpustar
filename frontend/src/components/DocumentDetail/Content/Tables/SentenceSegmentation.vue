<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
// components
import SentencePagination from '@/components/DocumentDetail/Content/SentencePagination.vue'
import SentencesOfDocument from '@/components/DocumentDetail/Content/SentenceSegmentation/SentencesOfDocument.vue'
// store
import { useProcessStore } from '@/stores/processStore'
import { useSentenceStore } from '@/stores/sentenceStore'

const route = useRoute()
const processStore = useProcessStore()
const sentenceStore = useSentenceStore()

const docId = computed(() => {
  const value = route.params.doc_id
  return typeof value === 'string' ? value : ''
})

const activeProcessing = computed(() => processStore.getSentenceSegmentationProcessByDocId(docId.value))
const activeProcessingId = computed(() => activeProcessing.value?.id ?? '')
const activeDocProcessKey = computed(() => {
  if (!docId.value || !activeProcessingId.value) {
    return ''
  }
  return `${docId.value}::${activeProcessingId.value}`
})
const sentenceItems = computed(() => {
  if (!docId.value || !activeProcessingId.value) {
    return []
  }
  return sentenceStore.getSentenceItems(docId.value, activeProcessingId.value)
})
const sentencePageSize = Number.parseInt(import.meta.env.VITE_SENTENCE_ITEM_PER_PAGE ?? '10', 10)
const highlightedSentenceIds = ref<string[]>([])
const currentPage = ref(1)
const pageOffsets = ref<Array<number | null>>([null])
const nextAfterStartOffset = ref<number | null>(null)
const pageLoading = ref(false)
const mutationLoading = ref(false)
const highlightedSentenceIdSet = computed(() => new Set(highlightedSentenceIds.value))
const sentenceActionLoading = computed(() => pageLoading.value || mutationLoading.value)
const hasPreviousPage = computed(() => currentPage.value > 1)
const hasNextPage = computed(() => nextAfterStartOffset.value !== null)

function setHighlightedSentenceIds(sentenceIds: string[]): void {
  const seen = new Set<string>()
  const normalized: string[] = []

  for (const sentenceId of sentenceIds) {
    if (!sentenceId || seen.has(sentenceId)) {
      continue
    }
    seen.add(sentenceId)
    normalized.push(sentenceId)
  }

  highlightedSentenceIds.value = normalized
}

function getPreviousSentenceId(sentenceId: string): string | null {
  const sentenceIndex = sentenceItems.value.findIndex((item) => item.id === sentenceId)
  if (sentenceIndex < 0) {
    return null
  }

  return sentenceItems.value[sentenceIndex - 1]?.id ?? null
}

function resetPagination(): void {
  currentPage.value = 1
  pageOffsets.value = [null]
  nextAfterStartOffset.value = null
}

async function loadSentencePage(
  offset: number | null,
  pageNumber: number,
  history: Array<number | null> = pageOffsets.value,
): Promise<void> {
  const currentDocId = docId.value
  const processingId = activeProcessingId.value
  if (!currentDocId || !processingId) {
    return
  }

  pageLoading.value = true

  try {
    const page = await sentenceStore.getSentences(currentDocId, processingId, offset, sentencePageSize)
    currentPage.value = pageNumber
    pageOffsets.value = history
    nextAfterStartOffset.value = page.nextAfterStartOffset ?? null
  } catch {
    // Keep current pagination state when a page request fails.
  } finally {
    pageLoading.value = false
  }
}

function refreshSentenceItems(): void {
  const currentPageOffset = pageOffsets.value[currentPage.value - 1] ?? null
  void loadSentencePage(currentPageOffset, currentPage.value)
}

function goToPreviousPage(): void {
  if (!hasPreviousPage.value || sentenceActionLoading.value) {
    return
  }

  setHighlightedSentenceIds([])
  const previousPageNumber = currentPage.value - 1
  const previousOffset = pageOffsets.value[previousPageNumber - 1] ?? null
  void loadSentencePage(previousOffset, previousPageNumber)
}

function goToNextPage(): void {
  if (!hasNextPage.value || sentenceActionLoading.value || nextAfterStartOffset.value === null) {
    return
  }

  setHighlightedSentenceIds([])
  const nextPageNumber = currentPage.value + 1
  const nextHistory = [...pageOffsets.value.slice(0, currentPage.value), nextAfterStartOffset.value]
  void loadSentencePage(nextAfterStartOffset.value, nextPageNumber, nextHistory)
}

function mergePreviousSentence(sentenceId: string): void {
  const previousSentenceId = getPreviousSentenceId(sentenceId)
  const currentDocId = docId.value
  const processingId = activeProcessingId.value
  if (!previousSentenceId || !currentDocId || !processingId) {
    return
  }

  mutationLoading.value = true
  void sentenceStore.mergeSentences([previousSentenceId, sentenceId])
    .then((mergedItem) => {
      setHighlightedSentenceIds([mergedItem.id])
      const currentPageOffset = pageOffsets.value[currentPage.value - 1] ?? null
      return loadSentencePage(currentPageOffset, currentPage.value)
    })
    .catch(() => undefined)
    .finally(() => {
      mutationLoading.value = false
    })
}

function clipSentence(sentenceId: string, splitOffset: number): void {
  const currentDocId = docId.value
  const processingId = activeProcessingId.value
  if (!currentDocId || !processingId) {
    return
  }

  mutationLoading.value = true
  void sentenceStore.clipSentence(sentenceId, splitOffset)
    .then((clippedItems) => {
      setHighlightedSentenceIds(clippedItems.slice(0, 2).map((item) => item.id))
      const currentPageOffset = pageOffsets.value[currentPage.value - 1] ?? null
      return loadSentencePage(currentPageOffset, currentPage.value)
    })
    .catch(() => undefined)
    .finally(() => {
      mutationLoading.value = false
    })
}

watch(
  activeDocProcessKey,
  (nextKey) => {
    highlightedSentenceIds.value = []
    resetPagination()
    if (!nextKey || !docId.value || !activeProcessingId.value) {
      return
    }

    refreshSentenceItems()
  },
  { immediate: true },
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

    <div v-else class="min-h-0 flex flex-1 flex-col overflow-hidden bg-background-elevated/15">
      <div class="scroll-area min-h-0 flex-1 space-y-2 overflow-y-auto">
        <SentencesOfDocument v-for="(item, index) in sentenceItems"
          :key="item.id" :item="item"
          :loading="sentenceActionLoading" :can-merge-prev="index > 0"
          :highlighted="highlightedSentenceIdSet.has(item.id)"
          @request-merge="mergePreviousSentence" @clip="clipSentence" />
      </div>

      <SentencePagination :current-page="currentPage" :item-count="sentenceItems.length"
        :has-previous="hasPreviousPage" :has-next="hasNextPage" :loading="sentenceActionLoading"
        @previous="goToPreviousPage" @next="goToNextPage" />
    </div>
  </div>
</template>
