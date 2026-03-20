<script setup lang="ts">
import DocumentSourceTextPanel from '@/components/DocumentDetail/Content/DocumentSourceTextPanel.vue'
import Lemmatization from '@/components/DocumentDetail/Content/Tables/Lemmatization.vue'
import SentenceSegmentation from '@/components/DocumentDetail/Content/Tables/SentenceSegmentation.vue'
import type { DocumentDetailViewMode } from '@/types/documentDetail'
import type { ProcessingState } from '@/types/processings'

const props = defineProps<{
  docId: string
  workspaceLoading: boolean
  viewMode: DocumentDetailViewMode
  sourceText: string
  sourceTextLoading: boolean
  segmentationRunning: ProcessingState | null
}>()

const emit = defineEmits<{
  segment: []
}>()
</script>

<template>
  <p
    v-if="props.workspaceLoading"
    class="text-sm text-text-muted">
    Loading...
  </p>

  <Lemmatization
    v-else-if="props.viewMode === 'lemma'"
    :doc-id="props.docId" />

  <SentenceSegmentation
    v-else-if="props.viewMode === 'sentence'"
    :doc-id="props.docId" />

  <DocumentSourceTextPanel
    v-else-if="props.viewMode === 'source'"
    :source-text="props.sourceText"
    :source-text-loading="props.sourceTextLoading"
    :segmentation-running="props.segmentationRunning"
    @segment="emit('segment')" />

  <p
    v-else
    class="text-sm text-text-muted">
    Document not found. Please remote it and upload again.
  </p>
</template>
