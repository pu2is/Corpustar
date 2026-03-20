<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
// store
import { useDocumentStore } from '@/stores/documentStore'
import { useProcessStore } from '@/stores/processStore'

const route = useRoute()
const documentStore = useDocumentStore()
const processStore = useProcessStore()

const docId = computed(() => {
  const param = route.params.doc_id
  return Array.isArray(param) ? (param[0] ?? '') : (param ?? '')
})

const documentItem = computed(() => documentStore.getDocumentById(docId.value))
const textPath = computed(() => documentItem.value?.textPath ?? '')
const segmentationRunning = computed(() => processStore.getSegmentationStateByDocId(docId.value))

const sourceText = ref('')
const sourceTextLoading = ref(false)

let textRequestId = 0

function segmentSentences(): void {
  if (!docId.value) {
    return
  }

  void processStore.segmentDocument(docId.value)
    .catch(() => undefined)
}

async function loadSourceText(textPath: string): Promise<void> {
  const requestId = ++textRequestId
  sourceTextLoading.value = true

  try {
    if (!window.electronAPI?.readDocumentText) {
      throw new Error('Document text reader unavailable. Restart is required.')
    }

    const content = await window.electronAPI.readDocumentText(textPath)
    if (requestId === textRequestId) {
      sourceText.value = content
    }
  } catch {
    if (requestId === textRequestId) {
      sourceText.value = ''
    }
  } finally {
    if (requestId === textRequestId) {
      sourceTextLoading.value = false
    }
  }
}

watch(textPath, (nextTextPath) => {
  if (!nextTextPath) {
    textRequestId += 1
    sourceText.value = ''
    sourceTextLoading.value = false
    return
  }
  void loadSourceText(nextTextPath)
  }, { immediate: true },
)
</script>

<template>
  <button type="button"
    :disabled="segmentationRunning === 'running'"
    class="w-fit rounded border px-3 py-1 mb-4 text-sm cursor-pointer disabled:opacity-60"
    @click="segmentSentences">
    Segment Sentences
  </button>

  <section class="min-h-0 flex flex-1 gap-3 overflow-hidden rounded border border-border/60 bg-background-elevated/25 p-3">
    <p v-if="sourceTextLoading"
      class="text-sm text-text-muted">
      Loading full text...
    </p>

    <p v-else-if="segmentationRunning === 'running'"
      class="text-sm text-text-muted">
      Running sentence segmentation...
    </p>


    <div v-else class="scroll-area min-h-0 flex-1 overflow-y-auto pr-1">
      <p class="text-sm whitespace-pre-wrap break-words text-violet-950">
        {{ sourceText || 'This document has no text content.' }}
      </p>
    </div>
  </section>
</template>
