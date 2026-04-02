<script setup lang="ts">
import type { SentenceItem } from '@/types/sentences';

const props = defineProps<{
  lastSentenceItem: SentenceItem | null
}>();
</script>

<template>
  <article class="mb-2 bg-violet-200/60 px-4 py-3 text-violet-950 backdrop-blur-md">
    <header class="space-y-1">
      <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-violet-800/80">
        Previous Sentence
      </p>
      <div :class="['inline-block min-h-4 text-xs transition-opacity duration-300',
        props.lastSentenceItem
          ? 'text-violet-900/80 opacity-100'
          : 'h-4 w-24 text-transparent opacity-100']">
        {{ props.lastSentenceItem ? `${props.lastSentenceItem.start_offset} - ${props.lastSentenceItem.end_offset}` : ' ' }}
      </div>
    </header>

    <!-- TODO: add a monitor for sentence changes watch if this container expanded or collapse. if expanded, that means h > 5. else collapse. use animation to smooth the transition of height -->
    <p :class="['mt-1 break-words transition-opacity duration-300',
      props.lastSentenceItem
        ? 'line-clamp-2 min-h-5 text-sm font-medium text-violet-950 opacity-100'
        : 'h-4 w-3/4 text-transparent opacity-100']">
      {{ props.lastSentenceItem?.source_text ?? ' ' }}
    </p>
  </article>
</template>
