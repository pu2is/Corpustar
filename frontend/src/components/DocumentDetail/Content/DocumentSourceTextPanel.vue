<script setup lang="ts">
import type { ProcessingState } from '@/types/processings'

const props = defineProps<{
  sourceText: string
  sourceTextLoading: boolean
  segmentationRunning: ProcessingState | null
}>()

const emit = defineEmits<{
  segment: []
}>()
</script>

<template>
  <button
    type="button"
    :disabled="props.segmentationRunning === 'running'"
    class="mb-4 w-fit cursor-pointer rounded border px-3 py-1 text-sm disabled:opacity-60"
    @click="emit('segment')">
    Segment Sentences
  </button>

  <section class="min-h-0 flex flex-1 overflow-hidden rounded border border-border/60 bg-background-elevated/25 p-3">
    <p
      v-if="props.sourceTextLoading"
      class="text-sm text-text-muted">
      Loading full text...
    </p>

    <p
      v-else-if="props.segmentationRunning === 'running'"
      class="text-sm text-text-muted">
      Running sentence segmentation...
    </p>

    <p
      v-else
      class="scroll-area min-h-0 flex-1 overflow-y-auto whitespace-pre-wrap break-words pr-1 text-sm text-violet-950">
      {{ props.sourceText || 'This document has no text content.' }}
    </p>
  </section>
</template>
