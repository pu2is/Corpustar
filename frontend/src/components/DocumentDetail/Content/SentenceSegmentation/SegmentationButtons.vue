<script setup lang="ts">
import { computed } from 'vue'
import type { SentenceItem } from '@/types/sentences'

type MergeDirection = 'prev' | 'next'

const props = defineProps<{
  loading: boolean
  canMerge: boolean
  pendingMergeDirection: MergeDirection | null
  pendingMergeTarget: SentenceItem | null
}>()

const emit = defineEmits<{
  merge: []
  clear: []
}>()

const mergeLabel = computed(() => {
  if (props.pendingMergeDirection === 'prev') {
    return 'Merge with Previous'
  }
  if (props.pendingMergeDirection === 'next') {
    return 'Merge with Next'
  }
  return 'Merge'
})

function triggerMerge(): void {
  emit('merge')
}

function clearPendingMerge(): void {
  emit('clear')
}
</script>

<template>
  <section class="flex shrink-0 gap-2">
    <button type="button"
      :disabled="loading || !canMerge"
      class="rounded border px-3 py-1 text-sm disabled:opacity-60"
      @click="triggerMerge">
      {{ mergeLabel }}
    </button>
    <button type="button"
      :disabled="loading || !pendingMergeDirection"
      class="rounded border px-3 py-1 text-sm disabled:opacity-60"
      @click="clearPendingMerge">
      Clear
    </button>
    <p v-if="pendingMergeTarget"
      class="self-center text-xs text-text-muted">
      Target: {{ pendingMergeTarget.startOffset }} - {{ pendingMergeTarget.endOffset }}
    </p>
  </section>
</template>
