<script setup lang="ts">
import { computed } from 'vue'
// stores
import { useFvgCandidateStore } from '@/stores/fvgCandidate'
// types
import type { DocItem } from '@/types/documents';
// icons
import { BookOpenText } from 'lucide-vue-next';

const props = defineProps<{
  document: DocItem;
  sentenceLength: number;
}>();

const fvgCandidateStore = useFvgCandidateStore()
const stats = computed(() => fvgCandidateStore.simpleStatistics)
</script>

<template>
  <header class="space-y-1 py-3">
    <h2 class="text-xl font-semibold text-violet-950">
      {{ document.display_name }}
    </h2>
    <template v-if="stats">
      <p class="inline-flex items-center gap-2 text-sm text-violet-500">
        <BookOpenText class="h-3.5 w-3.5" />
        {{ stats.num_sentences }} sentences &middot; {{ stats.num_fvg }} FVGs &middot; {{ stats.num_verb }} verbs &middot; {{ stats.num_aux }} auxiliaries
      </p>
    </template>
    <p v-else-if="sentenceLength < 0"
      class="inline-flex items-center gap-2 text-sm text-violet-500">
      <BookOpenText class="h-3.5 w-3.5" />
      {{ document.char_count }} characters
    </p>
  </header>
</template>