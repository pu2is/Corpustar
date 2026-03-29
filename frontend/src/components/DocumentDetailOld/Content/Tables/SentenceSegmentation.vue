<script setup lang="ts">
import { computed } from 'vue'
import SentenceSegmentationTable from '@/components/DocumentDetailOld/Content/SentenceSegmentation/SentenceSegmentationTable.vue'
import { useSentenceSegmentationTable } from '@/composables/documentDetail/useSentenceSegmentationTable'

const props = defineProps<{
  docId: string
}>()

const {
  activeProcessingId,
  sentenceItems,
  lastSentenceItem,
  lastSentenceLoading,
  currentPage,
  hasPreviousPage,
  hasNextPage,
  tableLoading,
  sentenceActionLoading,
  highlightedSentenceIds,
  showSegmentationLoading,
  tableRef,
  goToPreviousPage,
  goToNextPage,
  mergePreviousSentence,
  clipSentence,
} = useSentenceSegmentationTable(computed(() => props.docId))

void tableRef
</script>

<template>
  <div class="min-h-0 flex flex-1 flex-col gap-3 overflow-hidden">
    <p
      v-if="showSegmentationLoading"
      class="text-sm text-text-muted">
      Loading sentences...
    </p>

    <p
      v-else-if="!activeProcessingId"
      class="text-sm text-text-muted">
      Sentence segmentation result is not ready yet.
    </p>

    <p
      v-else-if="sentenceItems.length === 0"
      class="text-sm text-text-muted">
      No sentences in this segmentation result.
    </p>

    <SentenceSegmentationTable
      v-else
      ref="tableRef"
      :items="sentenceItems"
      :last-sentence-item="lastSentenceItem"
      :last-sentence-loading="lastSentenceLoading"
      :current-page="currentPage"
      :has-previous="hasPreviousPage"
      :has-next="hasNextPage"
      :table-loading="tableLoading"
      :sentence-action-loading="sentenceActionLoading"
      :highlighted-sentence-ids="highlightedSentenceIds"
      @previous="goToPreviousPage"
      @next="goToNextPage"
      @request-merge="mergePreviousSentence"
      @clip="clipSentence" />
  </div>
</template>
