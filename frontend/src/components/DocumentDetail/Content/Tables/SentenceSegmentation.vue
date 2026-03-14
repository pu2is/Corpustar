<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute } from 'vue-router'
// components
import SegmentationButtons from '@/components/DocumentDetail/Content/SentenceSegmentation/SegmentationButtons.vue'
import SentenceListItem from '@/components/DocumentDetail/Content/SentenceSegmentation/SentenceListItem.vue'
// store
import { useSentenceStore } from '@/stores/sentenceStore'

const route = useRoute()
const sentenceStore = useSentenceStore()

const {
  hasMoreByDocId,
  itemsByDocId,
  loadingByDocId,
  processingByDocId,
  selectedSentenceIdsByDocId,
} = storeToRefs(sentenceStore)

const docId = computed(() => {
  const value = route.params.doc_id
  return typeof value === 'string' ? value : ''
})

const sentenceItems = computed(() => itemsByDocId.value[docId.value] ?? [])
const sentenceHasMore = computed(() => hasMoreByDocId.value[docId.value] ?? false)
const sentenceLoading = computed(() => loadingByDocId.value[docId.value] ?? false)
const selectedSentenceIds = computed(() => selectedSentenceIdsByDocId.value[docId.value] ?? [])

function loadMoreSentences(): void {
  const processingId = processingByDocId.value[docId.value]?.id
  if (!docId.value || !processingId) {
    return
  }
  void sentenceStore
    .loadMoreSentences(docId.value, processingId)
    .catch(() => undefined)
}

function toggleSentenceSelection(sentenceId: string): void {
  if (!docId.value) {
    return
  }
  sentenceStore.toggleSentenceSelection(docId.value, sentenceId)
}

function clipSentence(sentenceId: string, splitOffset: number): void {
  if (!docId.value) {
    return
  }
  void sentenceStore.clipSentence(docId.value, sentenceId, splitOffset).catch(() => undefined)
}
</script>

<template>
  <div class="min-h-0 flex flex-1 flex-col gap-3 overflow-hidden rounded border border-border p-3">
    <p v-if="sentenceItems.length === 0"
      class="text-sm text-text-muted">
      No sentences in this segmentation result.
    </p>

    <div v-else class="min-h-0 flex flex-1 flex-col gap-3 overflow-hidden">
      <SegmentationButtons />

      <div class="scroll-area min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
        <SentenceListItem v-for="item in sentenceItems"
          :key="item.id" :item="item"
          :selected="selectedSentenceIds.includes(item.id)"
          :loading="sentenceLoading"
          @toggle-select="toggleSentenceSelection"
          @clip="clipSentence" />
      </div>

      <button v-if="sentenceHasMore"
        type="button"
        :disabled="sentenceLoading"
        class="shrink-0 rounded border px-3 py-1 text-sm disabled:opacity-60"
        @click="loadMoreSentences">
        Load More
      </button>
    </div>
  </div>
</template>
