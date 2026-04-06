<script setup lang="ts">
import { watch } from 'vue'
// composables
import { getIdFromUrl } from '@/composables/useRouteId'
// components
import FvgSentenceList from '@/components/DocumentDetail/FvgSentenceTable/FvgSentenceList.vue'
import FvgPagination from '@/components/DocumentDetail/FvgSentenceTable/FvgPagination.vue'
// stores
import { useProcessStore } from '@/stores/processStore'
import { useFvgCandidateStore } from '@/stores/fvgCandidate'

const docId = getIdFromUrl()
const processStore = useProcessStore()
const fvgCandidateStore = useFvgCandidateStore()

watch(
  [
    () => processStore.getSentenceSegmentationProcessByDocId(docId.value)?.id,
    () => processStore.getFvgProcessByDocId(docId.value)?.id,
    () => fvgCandidateStore.display,
  ],
  async ([segmentationId, fvgProcessId, display]) => {
    if (!segmentationId) return

    if (display === 'all') {
      await fvgCandidateStore.getSentences(segmentationId)
    } else if (display === 'detected' && fvgProcessId) {
      await fvgCandidateStore.getDetectedFvgCandidates(fvgProcessId)
    } else if (display === 'undetected' && fvgProcessId) {
      await fvgCandidateStore.getUndetectedFvgCandidates(fvgProcessId)
    }
  },
  { immediate: true },
)
</script>

<template>
  <section class="min-h-0 flex flex-1 flex-col overflow-hidden bg-background-elevated/15">
    <main data-fvg-sentence-scroll-area
      class="min-h-0 flex-1 overflow-y-auto p-2">
      <FvgSentenceList />
    </main>

    <FvgPagination />
  </section>
</template>
