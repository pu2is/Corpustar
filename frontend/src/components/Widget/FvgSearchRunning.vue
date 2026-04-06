<script setup lang="ts">
import { watch } from 'vue'
import { useProcessStore } from '@/stores/processStore'
import { useFvgCandidateStore } from '@/stores/fvgCandidate'
import { usePaginationStore } from '@/stores/local/paginationStore'

const processStore = useProcessStore()
const fvgCandidateStore = useFvgCandidateStore()
const paginationStore = usePaginationStore()

watch(() => processStore.fvgSearchRunning, (isRunning) => {
  if (!isRunning) {
    paginationStore.savePagination({ section: 'fvgSentenceTable', cursor: {} })
    fvgCandidateStore.changeDisplay('detected')
  }
})
</script>

<template>
  <Teleport to="body">
    <template v-if="processStore.fvgSearchRunning">
      <div class="fixed inset-0 z-40 bg-violet-200/40" />
      <div class="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 bg-violet-700 p-8 shadow-xl">
        <h2 class="mb-4 text-lg font-semibold text-yellow-300">FVG Search</h2>
        <p class="mb-6 text-sm text-yellow-200/80">
          FVG search is running. Please don't close the application.
        </p>
        <div class="flex justify-end">
          <span class="text-xs text-yellow-100/50">Running…</span>
        </div>
      </div>
    </template>
  </Teleport>
</template>