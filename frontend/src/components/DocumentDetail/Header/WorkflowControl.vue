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

const processItems = computed(() => processStore.getProcessesByDocId(docId.value))
const processItemCount = computed(() => processItems.value.length)
const displayTypeLabel = computed(() => sentenceStore.displayType === 'lemma' ? 'Lemma' : 'Source')

watch(docId, () => {
  sentenceStore.resetDisplayType()
}, { immediate: true })

watch([docId, processItemCount], ([, nextCount]) => {
  sentenceStore.ensureDisplayType(nextCount)
}, { immediate: true })

function startLemmatize(): void {
  if (!docId.value) {
    return
  }

  console.log('[WorkflowControl] TODO: implement lemmatize workflow after backend API and frontend flow are ready.', {
    docId: docId.value,
    nextStep: 'Call lemmatize process API and refresh process/sentence display state.',
  })
}

function toggleDisplayType(): void {
  sentenceStore.toggleDisplayType()
}
</script>

<template>
  <div v-if="processItemCount === 1">
    <button type="button"
      class="cursor-pointer rounded-[2px] bg-amber-400 px-4 py-1 text-lg font-medium text-violet-500 transition hover:bg-amber-400/85"
      @click="startLemmatize">
      <span class="relative inline-block">
        <span aria-hidden="true" class="absolute w-full bottom-[1px] left-[1px] text-cyan-300">
          Start Lemmatize
        </span>
        <span class="relative">Start Lemmatize</span>
      </span>
    </button>
  </div>

  <div v-else-if="processItemCount >=2">
    <button type="button"
      class="cursor-pointer rounded border border-border/70 px-3 py-1 text-xs font-medium text-violet-950 transition hover:bg-background-elevated/50"
      @click="toggleDisplayType">
      Display: {{ displayTypeLabel }}
    </button>
  </div>
</template>
