<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute } from 'vue-router'
// components
import SentenceListItem from '@/components/DocumentDetail/Content/SentenceSegmentation/SentenceListItem.vue'
// store
import { usePaginationStore } from '@/stores/local/paginationStore'
import { useProcessStore } from '@/stores/processStore'
import { useSentenceStore } from '@/stores/sentenceStore'

const DEFAULT_SENTENCE_PAGE_LIMIT = 20

const route = useRoute()
const paginationStore = usePaginationStore()
const processStore = useProcessStore()
const sentenceStore = useSentenceStore()

const { loading: processLoading } = storeToRefs(processStore)

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
const sentenceHasMore = computed(() => {
  if (!docId.value || !activeProcessingId.value) {
    return false
  }
  return paginationStore.hasMore(docId.value, activeProcessingId.value)
})
const sentenceLoading = computed(() => {
  if (!docId.value || !activeProcessingId.value) {
    return false
  }

  return paginationStore.isLoading(docId.value, activeProcessingId.value)
    || sentenceStore.isSentenceLoading(docId.value, activeProcessingId.value)
})
const actionLoading = computed(() => sentenceLoading.value || processLoading.value)
const sentenceListRef = ref<HTMLDivElement | null>(null)
const highlightedSentenceIds = ref<string[]>([])
const highlightedSentenceIdSet = computed(() => new Set(highlightedSentenceIds.value))

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

function restoreSentenceListScrollTop(scrollTop: number): void {
  void nextTick(() => {
    const listElement = sentenceListRef.value
    if (!listElement) {
      return
    }
    listElement.scrollTop = scrollTop
  })
}

function getPreviousSentenceId(sentenceId: string): string | null {
  const sentenceIndex = sentenceItems.value.findIndex((item) => item.id === sentenceId)
  if (sentenceIndex < 0) {
    return null
  }

  return sentenceItems.value[sentenceIndex - 1]?.id ?? null
}

function getCurrentSentenceLoadLimit(): number {
  return Math.max(sentenceItems.value.length, DEFAULT_SENTENCE_PAGE_LIMIT)
}

function loadMoreSentences(): void {
  const processingId = activeProcessingId.value
  if (!docId.value || !processingId) {
    return
  }
  void paginationStore.loadMore(docId.value, processingId).catch(() => undefined)
}

function runSentenceMutation<T>(
  operation: () => Promise<T>,
  onSuccess?: (result: T) => void,
): void {
  const currentDocId = docId.value
  const processingId = activeProcessingId.value
  if (!currentDocId || !processingId) {
    return
  }

  const currentScrollTop = sentenceListRef.value?.scrollTop ?? 0
  const currentLoadLimit = getCurrentSentenceLoadLimit()

  void operation()
    .then((result) => {
      onSuccess?.(result)
      return paginationStore.loadFirstPage(currentDocId, processingId, currentLoadLimit)
    })
    .then(() => {
      restoreSentenceListScrollTop(currentScrollTop)
    })
    .catch(() => undefined)
}

function mergePreviousSentence(sentenceId: string): void {
  const previousSentenceId = getPreviousSentenceId(sentenceId)
  if (!previousSentenceId) {
    return
  }

  runSentenceMutation(
    () => sentenceStore.mergeSentences([previousSentenceId, sentenceId]),
    (mergedItem) => {
      setHighlightedSentenceIds([mergedItem.id])
    },
  )
}

function clipSentence(sentenceId: string, splitOffset: number): void {
  runSentenceMutation(
    () => sentenceStore.clipSentence(sentenceId, splitOffset),
    (clippedItems) => {
      setHighlightedSentenceIds(clippedItems.slice(0, 2).map((item) => item.id))
    },
  )
}

watch(
  activeDocProcessKey,
  (nextKey) => {
    highlightedSentenceIds.value = []
    if (!nextKey || !docId.value || !activeProcessingId.value) {
      return
    }

    void paginationStore.loadFirstPage(docId.value, activeProcessingId.value).catch(() => undefined)
  },
  { immediate: true },
)
</script>

<template>
  <div class="min-h-0 flex flex-1 flex-col gap-3 overflow-hidden rounded border border-border p-3">
    <p v-if="sentenceItems.length === 0"
      class="text-sm text-text-muted">
      No sentences in this segmentation result.
    </p>

    <div v-else class="min-h-0 flex flex-1 flex-col gap-3 overflow-hidden">
      <div ref="sentenceListRef"
        class="scroll-area min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
        <SentenceListItem v-for="(item, index) in sentenceItems"
          :key="item.id" :item="item"
          :loading="actionLoading"
          :can-merge-prev="index > 0"
          :highlighted="highlightedSentenceIdSet.has(item.id)"
          @request-merge="mergePreviousSentence"
          @clip="clipSentence" />
      </div>

      <button v-if="sentenceHasMore"
        type="button"
        :disabled="actionLoading"
        class="shrink-0 rounded border px-3 py-1 text-sm disabled:opacity-60"
        @click="loadMoreSentences">
        Load More
      </button>
    </div>
  </div>
</template>
