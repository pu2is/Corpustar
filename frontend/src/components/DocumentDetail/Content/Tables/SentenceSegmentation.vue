<script setup lang="ts">
import { computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute } from 'vue-router'
// components
import SentenceListItem from '@/components/DocumentDetail/Content/SentenceSegmentation/SentenceListItem.vue'
// store
import { usePaginationStore } from '@/stores/local/paginationStore'
import { useProcessStore } from '@/stores/processStore'
import { useSentenceStore } from '@/stores/sentenceStore'

type MergeDirection = 'prev' | 'next'

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

function getAdjacentSentenceId(sentenceId: string, direction: MergeDirection): string | null {
  const sentenceIndex = sentenceItems.value.findIndex((item) => item.id === sentenceId)
  if (sentenceIndex < 0) {
    return null
  }

  if (direction === 'prev') {
    return sentenceItems.value[sentenceIndex - 1]?.id ?? null
  }

  return sentenceItems.value[sentenceIndex + 1]?.id ?? null
}

function loadMoreSentences(): void {
  const processingId = activeProcessingId.value
  if (!docId.value || !processingId) {
    return
  }
  void paginationStore.loadMore(docId.value, processingId).catch(() => undefined)
}

function mergeSentences(sentenceId: string, direction: MergeDirection): void {
  const processingId = activeProcessingId.value
  const adjacentSentenceId = getAdjacentSentenceId(sentenceId, direction)
  if (!docId.value || !processingId || !adjacentSentenceId) {
    return
  }

  const mergeSentenceIds = direction === 'prev'
    ? [adjacentSentenceId, sentenceId]
    : [sentenceId, adjacentSentenceId]

  void sentenceStore.mergeSentences(docId.value, processingId, mergeSentenceIds)
    .then(() => {
      return paginationStore.loadFirstPage(docId.value, processingId)
    })
    .catch(() => undefined)
}

function clipSentence(sentenceId: string, splitOffset: number): void {
  const processingId = activeProcessingId.value
  if (!docId.value || !processingId) {
    return
  }
  void sentenceStore.clipSentence(docId.value, processingId, sentenceId, splitOffset)
    .then(() => {
      return paginationStore.loadFirstPage(docId.value, processingId)
    })
    .catch(() => undefined)
}

watch(
  activeDocProcessKey,
  (nextKey) => {
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
      <div class="scroll-area min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
        <SentenceListItem v-for="(item, index) in sentenceItems"
          :key="item.id" :item="item"
          :loading="actionLoading"
          :can-merge-prev="index > 0"
          :can-merge-next="index < sentenceItems.length - 1"
          @request-merge="mergeSentences"
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
