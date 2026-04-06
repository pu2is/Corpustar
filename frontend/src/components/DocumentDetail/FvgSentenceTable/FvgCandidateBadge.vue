<script setup lang="ts">
import type { FvgCandidateItem } from '@/types/fvg'

defineProps<{
  fvgCandidateItem: FvgCandidateItem
}>()
</script>

<template>
  <span class="cursor-default inline-flex items-center gap-1 bg-violet-100 px-1 py-0.5 text-xs text-violet-700">
    {{ fvgCandidateItem.algo_verb_token }}
    <span class="text-violet-300">·</span>
    {{ fvgCandidateItem.algo_noun_token }}
    <template v-if="fvgCandidateItem.algo_prep_token">
      <span class="text-violet-300">·</span>
      {{ fvgCandidateItem.algo_prep_token }}
    </template>
  </span>
</template>
