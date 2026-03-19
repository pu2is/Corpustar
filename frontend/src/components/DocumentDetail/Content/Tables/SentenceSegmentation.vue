<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
// components
import SentencesOfDocument from '@/components/DocumentDetail/Content/SentenceSegmentation/SentencesOfDocument.vue'
// store
import { useProcessStore } from '@/stores/processStore'
import { useSentenceStore } from '@/stores/sentenceStore'

const route = useRoute()
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
const actionLoading = computed(() => (
  sentenceStore.isSentenceLoading(docId.value, activeProcessingId.value)
))
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

function getPreviousSentenceId(sentenceId: string): string | null {
  const sentenceIndex = sentenceItems.value.findIndex((item) => item.id === sentenceId)
  if (sentenceIndex < 0) {
    return null
  }

  return sentenceItems.value[sentenceIndex - 1]?.id ?? null
}

function refreshSentenceItems(): void {
  const currentDocId = docId.value
  const processingId = activeProcessingId.value
  if (!currentDocId || !processingId) {
    return
  }

  void sentenceStore.getSentences(currentDocId, processingId).catch(() => undefined)
}

function mergePreviousSentence(sentenceId: string): void {
  const previousSentenceId = getPreviousSentenceId(sentenceId)
  const currentDocId = docId.value
  const processingId = activeProcessingId.value
  if (!previousSentenceId || !currentDocId || !processingId) {
    return
  }

  void sentenceStore.mergeSentences([previousSentenceId, sentenceId])
    .then((mergedItem) => {
      setHighlightedSentenceIds([mergedItem.id])
      return sentenceStore.refreshLoadedSentences(currentDocId, processingId)
    })
    .catch(() => undefined)
}

function clipSentence(sentenceId: string, splitOffset: number): void {
  const currentDocId = docId.value
  const processingId = activeProcessingId.value
  if (!currentDocId || !processingId) {
    return
  }

  void sentenceStore.clipSentence(sentenceId, splitOffset)
    .then((clippedItems) => {
      setHighlightedSentenceIds(clippedItems.slice(0, 2).map((item) => item.id))
      return sentenceStore.refreshLoadedSentences(currentDocId, processingId)
    })
    .catch(() => undefined)
}

watch(
  activeDocProcessKey,
  (nextKey) => {
    highlightedSentenceIds.value = []
    if (!nextKey || !docId.value || !activeProcessingId.value) {
      return
    }

    refreshSentenceItems()
  },
  { immediate: true },
)
</script>

<template>
  <div class="min-h-0 flex flex-1 flex-col gap-3 overflow-hidden">
    <p v-if="sentenceItems.length === 0"
      class="text-sm text-text-muted">
      No sentences in this segmentation result.
    </p>

    <div v-else class="min-h-0 flex flex-1 flex-col gap-3 overflow-hidden">
      <div class="scroll-area min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
        <SentencesOfDocument v-for="(item, index) in sentenceItems"
          :key="item.id" :item="item"
          :loading="actionLoading" :can-merge-prev="index > 0"
          :highlighted="highlightedSentenceIdSet.has(item.id)"
          @request-merge="mergePreviousSentence" @clip="clipSentence" />
      </div>
    </div>
  </div>
</template>
