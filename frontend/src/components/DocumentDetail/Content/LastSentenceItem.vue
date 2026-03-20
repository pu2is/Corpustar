<script setup lang="ts">
import type { SentenceItem } from '@/types/sentences'

const props = defineProps<{
  item: SentenceItem | null
  loading: boolean
}>()
</script>

<template>
  <div v-if="props.item"
    class="sticky top-0 z-10 bg-violet-200/60 mb-2 px-4 py-3 text-violet-950 backdrop-blur-md">
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0 space-y-1">
        <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-violet-800/80">
          Previous Sentence
        </p>
        <p class="text-xs text-violet-900/80">
          {{ props.item.startOffset }} - {{ props.item.endOffset }}
        </p>
        <p class="line-clamp-2 break-words text-sm font-medium text-violet-950">
          {{ props.item.text }}
        </p>
      </div>

      <span v-if="props.loading"
        class="shrink-0 rounded bg-white/40 px-2 py-1 text-[11px] font-semibold text-violet-900/75">
        Updating
      </span>
    </div>
  </div>
</template>
