<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
// components
import LastSentenceItem from '@/components/DocumentDetail/Content/LastSentenceItem.vue'
import SentencePagination from '@/components/DocumentDetail/Content/SentencePagination.vue'
import SentencesOfDocument from '@/components/DocumentDetail/Content/SentenceSegmentation/SentencesOfDocument.vue'
// store
import { usePaginationStore } from '@/stores/local/paginationStore'
import { useProcessStore } from '@/stores/processStore'
import { useSentenceStore } from '@/stores/sentenceStore'
// types
import type { SentenceItem } from '@/types/sentences'

const route = useRoute()
const paginationStore = usePaginationStore()
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
const paginationEntry = computed(() => paginationStore.getPaginationEntry(docId.value))
const highlightedSentenceIds = ref<string[]>([])
const mutationLoading = ref(false)
const highlightedSentenceIdSet = computed(() => new Set(highlightedSentenceIds.value))
const pageLoading = computed(() => paginationEntry.value.loading)
const currentPage = computed(() => paginationEntry.value.currentPage)
const hasPreviousPage = computed(() => currentPage.value > 1)
const hasNextPage = computed(() => paginationEntry.value.hasMore)
const sentenceActionLoading = computed(() => pageLoading.value || mutationLoading.value)
const sentenceItemPerPage = Number.parseInt(import.meta.env.VITE_SENTENCE_ITEM_PER_PAGE ?? '10', 10)
const lastSentenceItem = ref<SentenceItem | null>(null)
const lastSentenceLoading = ref(false)
let lastSentenceRequestToken = 0

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
  const items = sentenceItems.value
  const sentenceIndex = items.findIndex((item) => item.id === sentenceId)

  if (sentenceIndex < 0) { return null }

  if (sentenceIndex > 0) { return items[sentenceIndex - 1]?.id ?? null }

  return items[0]?.startOffset === 0 ? null : lastSentenceItem.value?.id ?? null
}

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
      currentDocId, processingId,
      previousPageOffset, sentenceItemPerPage, false,
    )

    if (requestToken !== lastSentenceRequestToken) { return }

    lastSentenceItem.value = previousPage.items[previousPage.items.length - 1] ?? null
  } catch {
    if (requestToken !== lastSentenceRequestToken) { return }

    lastSentenceItem.value = null
  } finally {
    if (requestToken === lastSentenceRequestToken) {
      lastSentenceLoading.value = false
    }
  }
}

function goToPreviousPage(): void {
  const currentDocId = docId.value
  const processingId = activeProcessingId.value
  if (!currentDocId || !processingId || !hasPreviousPage.value || sentenceActionLoading.value) {
    return
  }

  setHighlightedSentenceIds([])
  void paginationStore.goToPreviousPage(currentDocId, processingId)
}

function goToNextPage(): void {
  const currentDocId = docId.value
  const processingId = activeProcessingId.value
  if (!currentDocId || !processingId || !hasNextPage.value || sentenceActionLoading.value) {
    return
  }

  setHighlightedSentenceIds([])
  void paginationStore.goToNextPage(currentDocId, processingId)
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
      return paginationStore.refreshCurrentPage(currentDocId, processingId)
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
      return paginationStore.refreshCurrentPage(currentDocId, processingId)
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
    lastSentenceItem.value = null
    lastSentenceLoading.value = false
    if (!nextKey || !docId.value || !activeProcessingId.value) {
      return
    }

    void paginationStore.initializeDocumentPagination(docId.value, activeProcessingId.value)
  },
  { immediate: true },
)

watch(
  [activeDocProcessKey, currentPage,
    () => sentenceItems.value[0]?.id ?? '',
    () => sentenceItems.value[0]?.startOffset ?? 0,],
  () => { void loadLastSentenceItem()},
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
      <div class="scroll-area min-h-0 flex-1 overflow-y-auto">
        <LastSentenceItem :item="lastSentenceItem"
          :loading="sentenceActionLoading || lastSentenceLoading" />

        <div class="space-y-2">
          <SentencesOfDocument v-for="(item, index) in sentenceItems"
            :key="item.id" :item="item"
            :loading="sentenceActionLoading"
            :can-merge-prev="index > 0 || (index === 0 && item.startOffset > 0 && lastSentenceItem !== null)"
            :highlighted="highlightedSentenceIdSet.has(item.id)"
            @request-merge="mergePreviousSentence" @clip="clipSentence" />
        </div>
      </div>

      <SentencePagination :current-page="currentPage" :item-count="sentenceItems.length"
        :has-previous="hasPreviousPage" :has-next="hasNextPage" :loading="sentenceActionLoading"
        @previous="goToPreviousPage" @next="goToNextPage" />
    </div>
  </div>
</template>
