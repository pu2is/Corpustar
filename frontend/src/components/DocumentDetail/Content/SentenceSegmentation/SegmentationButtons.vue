<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useRoute } from 'vue-router'

import { useSentenceStore } from '@/stores/sentenceStore'

const route = useRoute()
const sentenceStore = useSentenceStore()
const { loadingByDocId, processingByDocId, selectedSentenceIdsByDocId } = storeToRefs(sentenceStore)

const docId = computed(() => {
  const value = route.params.doc_id
  return typeof value === 'string' ? value : ''
})

const activeProcessing = computed(() => processingByDocId.value[docId.value] ?? null)
const sentenceLoading = computed(() => loadingByDocId.value[docId.value] ?? false)
const selectedSentenceIds = computed(() => selectedSentenceIdsByDocId.value[docId.value] ?? [])
const canMerge = computed(() => selectedSentenceIds.value.length >= 2)

function mergeSelectedSentences(): void {
  if (!docId.value) {
    return
  }
  void sentenceStore.mergeSelected(docId.value).catch(() => undefined)
}
</script>

<template>
  <section class="flex shrink-0 gap-2">
    <button v-if="activeProcessing"
      type="button"
      :disabled="sentenceLoading || !canMerge"
      class="rounded border px-3 py-1 text-sm disabled:opacity-60"
      @click="mergeSelectedSentences">
      Merge Selected
    </button>
  </section>
</template>
