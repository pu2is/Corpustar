<script setup lang="ts">
import { computed, ref } from 'vue'
import { useSentenceStore } from '@/stores/sentenceStore'

const sentenceStore = useSentenceStore()
const sentenceItems = computed(() => sentenceStore.sentences)

const highlightIndex = ref(3);

// actions: merge, split, correct
</script>

<template>
  <article v-for="(item, index) in sentenceItems"
    :key="item.id"
    class="mb-2 border p-2 transition-colors duration-200"
    :class="index === highlightIndex ? 'border-emerald-500 bg-emerald-50/60' : 'border-border'">
    <p class="text-xs text-text-muted">
      {{ item.start_offset }} - {{ item.end_offset }}
    </p>

    <p class="mt-1 text-sm">
      {{ item.source_text }}
    </p>

    <div class="mt-2 flex gap-2">
      <button type="button"
        class="cursor-pointer bg-violet-200 px-3 py-0.5 text-xs text-violet-700">
        Merge Prev
      </button>
      <button type="button"
        class="cursor-pointer bg-fuchsia-100 px-3 py-0.5 text-xs text-fuchsia-700">
        Clip
      </button>
    </div>
  </article>
</template>
