<script setup lang="ts">
import { watch } from 'vue'
// composables
import { getIdFromUrl } from '@/composables/useRouteId'
// components
import FvgSentenceList from '@/components/DocumentDetail/FvgSentenceTable/FvgSentenceList.vue'
import FvgPagination from '@/components/DocumentDetail/FvgSentenceTable/FvgPagination.vue'
import FuzzySearch from '@/components/DocumentDetail/FvgSentenceTable/FuzzySearch.vue'
// stores
import { useProcessStore } from '@/stores/processStore'
import { useFvgCandidateStore } from '@/stores/fvgCandidate'
import { usePaginationStore } from '@/stores/local/paginationStore'
import type { FvgSentenceTableMode } from '@/stores/local/paginationStore'

const docId = getIdFromUrl()
const processStore = useProcessStore()
const fvgCandidateStore = useFvgCandidateStore()
const paginationStore = usePaginationStore()

function displayToMode(d: typeof fvgCandidateStore.display): FvgSentenceTableMode {
  if (d === 'detected') return 'matched'
  if (d === 'undetected') return 'unmatched'
  return 'all'
}

// Only watch process IDs — display-mode changes are handled exclusively by FvgPagination's
// watch(display) which correctly restores the saved cursor for each mode. Including display
// here caused a race: both watchers fired on mode-switch, FvgSentenceTable always won with
// cursor=null and wiped the cursor FvgPagination had just restored.
watch(
  [
    () => processStore.getSentenceSegmentationProcessByDocId(docId.value)?.id,
    () => processStore.getFvgProcessByDocId(docId.value)?.id,
  ],
  async ([segmentationId, fvgProcessId]) => {
    if (!segmentationId) return
    const display = fvgCandidateStore.display
    const verbFilter = fvgCandidateStore.verbFilter
    const mode = displayToMode(display)
    const savedCursor = paginationStore.paginationInfo.fvgSentenceTable[mode]?.currentCursor ?? null

    if (display === 'all') {
      await fvgCandidateStore.getSentences(segmentationId, savedCursor, undefined, verbFilter)
    } else if (display === 'detected' && fvgProcessId) {
      await fvgCandidateStore.getDetectedFvgCandidates(fvgProcessId, savedCursor, undefined, verbFilter)
    } else if (display === 'undetected' && fvgProcessId) {
      await fvgCandidateStore.getUndetectedFvgCandidates(fvgProcessId, savedCursor, undefined, verbFilter)
    }
  },
  { immediate: true },
)
</script>

<template>
  <section class="min-h-0 flex flex-1 flex-col overflow-hidden bg-background-elevated/15">
    <FuzzySearch />
    <main data-fvg-sentence-scroll-area
      class="min-h-0 flex-1 overflow-y-auto p-2">
      <FvgSentenceList />
    </main>
    <FvgPagination />
  </section>
</template>
