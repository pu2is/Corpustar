<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import DocumentSourceTextPanel from '@/components/DocumentDetail/Content/DocumentSourceTextPanel.vue'
import SentenceSegmentation from '@/components/DocumentDetail/Content/Tables/SentenceSegmentation.vue'
import { useDocumentStore } from '@/stores/documentStore'
import { usePaginationStore } from '@/stores/local/paginationStore'
import { useProcessStore } from '@/stores/processStore'

const route = useRoute()
const documentStore = useDocumentStore()
const paginationStore = usePaginationStore()
const processStore = useProcessStore()
const workspaceLoading = ref(false)

const docId = computed(() => {
  const value = route.params.doc_id
  return typeof value === 'string' ? value : ''
})

const documentItem = computed(() => documentStore.getDocumentById(docId.value))
const processes = computed(() => processStore.getProcessesByDocId(docId.value))
const savedSentenceAnchor = computed(() => paginationStore.getSentenceAnchor(docId.value))
const activeProcessing = computed(() => processStore.getSentenceSegmentationProcessByDocId(docId.value))
const hasSourceText = computed(() => Boolean(documentItem.value?.textPath?.trim()))
const hasAnyProcessing = computed(() => processes.value.length > 0)
const showSentenceTable = computed(() => {
  if (!documentItem.value || !activeProcessing.value) {
    return false
  }

  if (savedSentenceAnchor.value) {
    return true
  }

  return hasAnyProcessing.value
})
const showSourceText = computed(() => !showSentenceTable.value && hasSourceText.value)

async function initializeAnalyzeWorkspace(targetDocId: string): Promise<void> {
  workspaceLoading.value = true

  try {
    paginationStore.hydrateFromLocalStorage()

    const hasDocumentInStore = documentStore.getDocumentById(targetDocId) !== null
    if (!hasDocumentInStore) {
      await documentStore.getAllDocuments()
    }

    await processStore.getAllProcesses()
  } catch {
    // Store actions already preserve error state for rendering.
  } finally {
    workspaceLoading.value = false
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
  <p v-if="workspaceLoading"
    class="text-sm text-text-muted">
    Loading...
  </p>

  <SentenceSegmentation v-else-if="showSentenceTable" />

  <DocumentSourceTextPanel v-else-if="showSourceText" />

  <div v-else
    class="space-y-2">
    <p class="text-sm text-text-muted">
      Document not found. Please remote it and upload again.
    </p>
  </div>
</template>
