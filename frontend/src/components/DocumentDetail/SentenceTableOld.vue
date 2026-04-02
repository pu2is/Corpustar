<script setup lang="ts">
import { computed, watch } from 'vue'

import SentenceRow from '@/components/DocumentDetail/SentenceTableOld/SentenceRow.vue'

import { useProcessStore } from '@/stores/processStore'
import { useSentenceStore } from '@/stores/sentenceStore'
import type { SentenceItem } from '@/types/sentences'
import { usePaginationStore } from '@/stores/local/paginationStore'

const props = defineProps<{
  docId: string
}>()

const paginationStore = usePaginationStore()
const processStore = useProcessStore()
const sentenceStore = useSentenceStore()

const activeProcessing = computed(() => processStore.getSentenceSegmentationProcessByDocId(props.docId))
const activeProcessingId = computed(() => activeProcessing.value?.id ?? '')
const activeDocProcessKey = computed(() => (
  props.docId && activeProcessingId.value ? `${props.docId}::${activeProcessingId.value}` : ''
))
const segmentationState = computed(() => (
  processStore
    .getProcessByDocId(props.docId)
    .find((process) => process.type === 'sentence_segmentation')?.state ?? null
))

const paginationEntry = computed(() => paginationStore.getPaginationEntry(props.docId, 'sentence'))
const paginationReady = computed(() => paginationEntry.value.processingId === activeProcessingId.value)
const pageLoading = computed(() => paginationEntry.value.loading)
const tableLoading = computed(() => pageLoading.value)
const currentPage = computed(() => paginationEntry.value.currentPage)
const hasPreviousPage = computed(() => currentPage.value > 1)
const hasNextPage = computed(() => paginationEntry.value.hasMore)

const sentenceItemIds = computed(() => paginationEntry.value.pageItemIds)
const storedSentenceMap = computed(() => {
  if (!props.docId || !activeProcessingId.value) {
    return new Map<string, SentenceItem>()
  }

  return new Map<string, SentenceItem>(
    sentenceStore
      .getSentenceItems(props.docId, activeProcessingId.value)
      .map((item) => [item.id, item]),
  )
})
const sentenceItems = computed(() => {
  if (!props.docId || !activeProcessingId.value) {
    return []
  }

  if (sentenceItemIds.value.length === 0) {
    return Array.from(storedSentenceMap.value.values())
  }

  return sentenceItemIds.value
    .map((itemId) => storedSentenceMap.value.get(itemId))
    .filter((item): item is SentenceItem => item !== undefined)
})

const showSegmentationLoading = computed(() => (
  segmentationState.value === 'running'
  || (Boolean(activeProcessingId.value) && (!paginationReady.value || (pageLoading.value && sentenceItems.value.length === 0)))
))

async function goToPreviousPage(): Promise<void> {
  const processingId = activeProcessingId.value
  if (!props.docId || !processingId || !hasPreviousPage.value || tableLoading.value) {
    return
  }

  await paginationStore.goToPreviousPage(props.docId, processingId, 'sentence')
}

async function goToNextPage(): Promise<void> {
  const processingId = activeProcessingId.value
  if (!props.docId || !processingId || !hasNextPage.value || tableLoading.value) {
    return
  }

  await paginationStore.goToNextPage(props.docId, processingId, 'sentence')
}

watch(
  activeDocProcessKey,
  async (nextKey) => {
    if (!nextKey || !props.docId || !activeProcessingId.value) {
      return
    }

    await paginationStore.initializeDocumentPagination(props.docId, activeProcessingId.value, 'sentence')
  },
  { immediate: true },
)
</script>

<template>
  <section class="min-h-0 flex flex-1 flex-col overflow-hidden bg-background-elevated/15">
    <p v-if="showSegmentationLoading"
      class="p-3 text-sm text-text-muted">
      Loading sentences...
    </p>
    <p v-else-if="sentenceItems.length === 0"
      class="p-3 text-sm text-text-muted">
      No sentences in this segmentation result.
    </p>

    <template v-else>
      <SentenceRow
        :sentence-items="sentenceItems" />

      <footer class="bg-violet-200/60 px-4 py-3 text-violet-950 shadow-[0_16px_36px_-24px_rgba(109,40,217,0.9)] backdrop-blur-md">
        <div class="flex items-center justify-between gap-3">
          <p class="text-sm font-medium">
            Page {{ currentPage }}
          </p>
          <div class="flex items-center gap-2">
            <button type="button"
              :disabled="tableLoading || !hasPreviousPage"
              class="cursor-pointer bg-white/45 px-3 py-1.5 text-xs font-semibold text-violet-900 transition hover:bg-white/70 disabled:cursor-not-allowed disabled:opacity-45"
              @click="void goToPreviousPage()">
              Prev
            </button>
            <button type="button"
              :disabled="tableLoading || !hasNextPage"
              class="cursor-pointer bg-violet-500 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-violet-600/85 disabled:cursor-not-allowed disabled:opacity-45"
              @click="void goToNextPage()">
              Next
            </button>
          </div>
        </div>
      </footer>
    </template>
  </section>
</template>
