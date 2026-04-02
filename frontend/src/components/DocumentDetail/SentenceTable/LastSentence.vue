<script setup lang="ts">
import { computed } from 'vue'
// stores
import { useSentenceStore } from '@/stores/sentenceStore';

const sentenceStore = useSentenceStore();
const sentenceList = computed(() => sentenceStore.sentenceList);

</script>

<template>
  <header class="bg-violet-200/60 px-4 py-3 text-violet-950 backdrop-blur-md">
    <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-violet-800/80">
      Previous Sentence
    </p>
    <p class="mt-1 text-sm font-medium text-violet-950">
      {{ sentenceList.prevSentence?.source_text ?? '' }}
    </p>
  </header>
</template>
