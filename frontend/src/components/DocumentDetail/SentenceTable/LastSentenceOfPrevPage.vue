<script setup lang="ts">
import type { SentenceItem } from '@/types/sentences';

const props = defineProps<{
  lastSentenceItem: SentenceItem
  isUpdating: boolean
}>();
</script>

<template>
  <article class="mb-2 flex items-start justify-between gap-3 bg-violet-200/60 px-4 py-3 text-violet-950 backdrop-blur-md">
    <div class="space-y-1">
      <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-violet-800/80">
        Previous Sentence
      </p>
      <p class="text-xs text-violet-900/80">
        {{ props.lastSentenceItem.start_offset }} - {{ props.lastSentenceItem.end_offset }}
      </p>
      <p class="line-clamp-2 break-words text-sm font-medium text-violet-950">
        {{ props.lastSentenceItem.source_text }}
      </p>
    </div>
    <span v-if="props.isUpdating"
      class="shrink-0 rounded bg-white/40 px-2 py-1 text-[11px] font-semibold text-violet-900/75">
      Updating
    </span>
  </article>
</template>
