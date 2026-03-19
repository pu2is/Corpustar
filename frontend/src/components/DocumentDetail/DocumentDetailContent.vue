<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'

import DocumentSourceTextPanel from '@/components/DocumentDetail/Content/DocumentSourceTextPanel.vue'
import SentenceTable from '@/components/DocumentDetail/Content/SentenceTable.vue'
import { useDocumentStore } from '@/stores/documentStore'
import { useProcessStore } from '@/stores/processStore'

const route = useRoute()
const documentStore = useDocumentStore()
const processStore = useProcessStore()

const docId = computed(() => {
  const value = route.params.doc_id
  return typeof value === 'string' ? value : ''
})

const documentItem = computed(() => documentStore.getDocumentById(docId.value))
const processes = computed(() => processStore.getProcessesByDocId(docId.value))
const activeProcessing = computed(() => processStore.getSentenceSegmentationProcessByDocId(docId.value))
const pageLoading = computed(() => processes.value.some((process) => process.state === 'running'))
const docHasNoProcessing = computed(() => Boolean(documentItem.value) && !activeProcessing.value)

async function initializeAnalyzeWorkspace(targetDocId: string): Promise<void> {
  try {
    const hasDocumentInStore = documentStore.getDocumentById(targetDocId) !== null
    if (!hasDocumentInStore) {
      await documentStore.getAllDocuments()
    }

    await processStore.getAllProcesses()
  } catch {
    // Store actions already preserve error state for rendering.
  }
}

watch(
  docId,
  (nextDocId) => {
    if (!nextDocId) {
      return
    }
    void initializeAnalyzeWorkspace(nextDocId)
  },
  { immediate: true },
)
</script>

<template>
  <p v-if="pageLoading"
    class="text-sm text-text-muted">
    Loading...
  </p>

  <DocumentSourceTextPanel v-else-if="docHasNoProcessing" />

  <SentenceTable v-else-if="documentItem" />

  <div v-else
    class="space-y-2">
    <p class="text-sm text-text-muted">
      Document not found.
    </p>
  </div>
</template>
