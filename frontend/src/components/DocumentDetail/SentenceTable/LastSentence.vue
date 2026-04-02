<script setup lang="ts">
const props = defineProps<{
  lastSentenceText: string
}>()
</script>

<template>
  <header class="bg-violet-200/60 px-4 py-3 text-violet-950 backdrop-blur-md">
    <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-violet-800/80">
      Previous Sentence
    </p>
    <p class="mt-1 text-sm font-medium text-violet-950">
      {{ props.lastSentenceText }}
    </p>
  </header>
</template>
