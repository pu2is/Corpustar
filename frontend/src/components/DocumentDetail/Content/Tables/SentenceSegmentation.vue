<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute } from 'vue-router'
// components
import SegmentationButtons from '@/components/DocumentDetail/Content/SentenceSegmentation/SegmentationButtons.vue'
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

const selectedSentenceId = ref<string | null>(null)
const pendingMergeDirection = ref<MergeDirection | null>(null)
const pendingMergeTargetId = ref<string | null>(null)

const sentenceItemById = computed(() => {
  return new Map(sentenceItems.value.map((item) => [item.id, item] as const))
})
const pendingMergeTarget = computed(() => {
  if (!pendingMergeTargetId.value) {
    return null
  }
  return sentenceItemById.value.get(pendingMergeTargetId.value) ?? null
})
const canMerge = computed(() => {
  return Boolean(
    selectedSentenceId.value
    && pendingMergeDirection.value
    && pendingMergeTargetId.value,
  )
})

function clearPendingMerge(): void {
  selectedSentenceId.value = null
  pendingMergeDirection.value = null
  pendingMergeTargetId.value = null
}

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

function selectSentence(sentenceId: string): void {
  if (!sentenceId) {
    return
  }

  if (selectedSentenceId.value === sentenceId) {
    clearPendingMerge()
    return
  }

  selectedSentenceId.value = sentenceId
  pendingMergeDirection.value = null
  pendingMergeTargetId.value = null
}

function requestMerge(sentenceId: string, direction: MergeDirection): void {
  selectedSentenceId.value = sentenceId
  pendingMergeDirection.value = direction
  pendingMergeTargetId.value = getAdjacentSentenceId(sentenceId, direction)
}

function mergePendingSentences(): void {
  const processingId = activeProcessingId.value
  if (!docId.value || !processingId || !selectedSentenceId.value || !pendingMergeTargetId.value || !pendingMergeDirection.value) {
    return
  }

  const selectedId = selectedSentenceId.value
  const targetId = pendingMergeTargetId.value
  const mergeSentenceIds = pendingMergeDirection.value === 'prev'
    ? [targetId, selectedId]
    : [selectedId, targetId]

  void sentenceStore.mergeSentences(docId.value, processingId, mergeSentenceIds)
    .then(() => {
      return paginationStore.loadFirstPage(docId.value, processingId)
    })
    .then(() => {
      clearPendingMerge()
    })
    .catch(() => undefined)
}

function clipSentence(sentenceId: string, splitOffset: number): void {
  const processingId = activeProcessingId.value
  if (!docId.value || !processingId) {
    return
  }
  clearPendingMerge()
  void sentenceStore.clipSentence(docId.value, processingId, sentenceId, splitOffset)
    .then(() => {
      return paginationStore.loadFirstPage(docId.value, processingId)
    })
    .catch(() => undefined)
}

watch(
  activeDocProcessKey,
  (nextKey) => {
    clearPendingMerge()
    if (!nextKey || !docId.value || !activeProcessingId.value) {
      return
    }

    void paginationStore.loadFirstPage(docId.value, activeProcessingId.value).catch(() => undefined)
  },
  { immediate: true },
)

watch(sentenceItems, (nextItems) => {
  if (!nextItems.length) {
    clearPendingMerge()
    return
  }

  const itemIds = new Set(nextItems.map((item) => item.id))
  const selectedId = selectedSentenceId.value
  if (selectedId && !itemIds.has(selectedId)) {
    clearPendingMerge()
    return
  }

  const pendingTargetId = pendingMergeTargetId.value
  if (pendingTargetId && !itemIds.has(pendingTargetId)) {
    pendingMergeDirection.value = null
    pendingMergeTargetId.value = null
  }
})
</script>

<template>
  <div class="min-h-0 flex flex-1 flex-col gap-3 overflow-hidden rounded border border-border p-3">
    <p v-if="sentenceItems.length === 0"
      class="text-sm text-text-muted">
      No sentences in this segmentation result.
    </p>

    <div v-else class="min-h-0 flex flex-1 flex-col gap-3 overflow-hidden">
      <SegmentationButtons v-if="activeProcessing"
        :loading="actionLoading"
        :can-merge="canMerge"
        :pending-merge-direction="pendingMergeDirection"
        :pending-merge-target="pendingMergeTarget"
        @merge="mergePendingSentences"
        @clear="clearPendingMerge" />

      <div class="scroll-area min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
        <SentenceListItem v-for="(item, index) in sentenceItems"
          :key="item.id" :item="item"
          :selected="selectedSentenceId === item.id"
          :loading="actionLoading"
          :can-merge-prev="index > 0"
          :can-merge-next="index < sentenceItems.length - 1"
          @select-sentence="selectSentence"
          @request-merge="requestMerge"
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
