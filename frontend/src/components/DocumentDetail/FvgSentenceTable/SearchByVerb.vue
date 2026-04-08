<script setup lang="ts">
import { ref } from 'vue'
import { Search, X } from 'lucide-vue-next'
import { useFvgCandidateStore } from '@/stores/fvgCandidate'
import { useProcessStore } from '@/stores/processStore'
import { getIdFromUrl } from '@/composables/useRouteId'

const docId = getIdFromUrl()
const fvgCandidateStore = useFvgCandidateStore()
const processStore = useProcessStore()

const inputValue = ref(fvgCandidateStore.verbFilter ?? '')

async function search(): Promise<void> {
  const verb = inputValue.value.trim() || null
  fvgCandidateStore.setVerbFilter(verb)

  const segmentationId = processStore.getSentenceSegmentationProcessByDocId(docId.value)?.id ?? ''
  const fvgProcessId = processStore.getFvgProcessByDocId(docId.value)?.id ?? ''

  if (fvgCandidateStore.display === 'detected' && fvgProcessId) {
    await fvgCandidateStore.getDetectedFvgCandidates(fvgProcessId, null, undefined, verb)
  } else if (fvgCandidateStore.display === 'undetected' && fvgProcessId) {
    await fvgCandidateStore.getUndetectedFvgCandidates(fvgProcessId, null, undefined, verb)
  } else if (segmentationId) {
    await fvgCandidateStore.getSentences(segmentationId, null, undefined, verb)
  }
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'Enter') void search()
  if (event.key === 'Escape') void clear()
}

async function clear(): Promise<void> {
  inputValue.value = ''
  await search()
}
</script>

<template>
  <header class="shrink-0 flex items-center gap-2 bg-background-elevated px-3 py-2">
    <div class="relative flex-1">
      <input v-model="inputValue"
        type="text" placeholder="Search by verb lemma (base form)..."
        class="h-8 w-full border border-secondary/20 bg-background px-3 pr-8 text-sm text-violet-950 outline-none transition-colors placeholder:text-text-muted/70 focus:border-secondary/50"
        @keydown="handleKeydown" />
      <button v-if="inputValue"
        type="button"
        class="absolute right-1 top-1/2 inline-flex h-6 w-6 -translate-y-1/2 cursor-pointer items-center justify-center text-text-muted transition-colors hover:text-violet-950"
        aria-label="Clear"
        @click="void clear()">
        <X class="h-3.5 w-3.5" />
      </button>
    </div>
    <button type="button"
      class="shrink-0 inline-flex items-center gap-1.5 bg-violet-500 px-3 h-8 text-xs font-semibold text-white transition-colors hover:bg-violet-600 cursor-pointer"
      @click="void search()">
      <Search class="h-3.5 w-3.5" />
      Search
    </button>
  </header>
</template>
