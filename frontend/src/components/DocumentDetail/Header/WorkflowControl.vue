<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useProcessStore } from '@/stores/processStore'
import { useSentenceStore } from '@/stores/sentenceStore'

const route = useRoute()
const processStore = useProcessStore()
const sentenceStore = useSentenceStore()

const docId = computed(() => {
  const param = route.params.doc_id
  return Array.isArray(param) ? (param[0] ?? '') : (param ?? '')
})

const segmentationProcess = computed(() => processStore.getSentenceSegmentationProcessByDocId(docId.value))
const lemmatizeProcess = computed(() => processStore.getLemmatizeProcessBySegmentationId(
  docId.value,
  segmentationProcess.value?.id ?? '',
))
const canDisplayLemma = computed(() => lemmatizeProcess.value?.state === 'succeed')
const lemmatizeRunning = computed(() => lemmatizeProcess.value?.state === 'running')
const lemmatizeFailed = computed(() => lemmatizeProcess.value?.state === 'failed')
const displayTypeLabel = computed(() => sentenceStore.displayType === 'lemma' ? 'Lemma' : 'Source')

watch(docId, () => {
  sentenceStore.resetDisplayType()
}, { immediate: true })

watch([docId, canDisplayLemma], ([, nextCanDisplayLemma]) => {
  sentenceStore.ensureDisplayType(nextCanDisplayLemma)
}, { immediate: true })

function startLemmatize(): void {
  if (!docId.value || !segmentationProcess.value || lemmatizeRunning.value) {
    return
  }

  void processStore.lemmatizeSegmentation(docId.value, segmentationProcess.value.id)
}

function toggleDisplayType(): void {
  sentenceStore.toggleDisplayType()
}
</script>

<template>
  <div v-if="segmentationProcess && !canDisplayLemma">
    <button type="button"
      :disabled="lemmatizeRunning"
      class="cursor-pointer rounded-[2px] bg-amber-400 px-4 py-1 text-lg font-medium text-violet-500 transition hover:bg-amber-400/85 disabled:cursor-not-allowed disabled:opacity-60"
      @click="startLemmatize">
      <span class="relative inline-block">
        <span aria-hidden="true" class="absolute w-full bottom-[1px] left-[1px] text-cyan-300 whitespace-nowrap">
          {{ lemmatizeRunning ? 'Lemmatizing...' : (lemmatizeFailed ? 'Retry Lemmatize' : 'Start Lemmatize') }}
        </span>
        <span class="relative whitespace-nowrap">
          {{ lemmatizeRunning ? 'Lemmatizing...' : (lemmatizeFailed ? 'Retry Lemmatize' : 'Start Lemmatize') }}
        </span>
      </span>
    </button>
  </div>

  <div v-else-if="canDisplayLemma">
    <button type="button"
      class="cursor-pointer rounded border border-border/70 px-3 py-1 text-xs font-medium text-violet-950 transition hover:bg-background-elevated/50"
      @click="toggleDisplayType">
      Display: {{ displayTypeLabel }}
    </button>
  </div>
</template>
