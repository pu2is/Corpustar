<script setup lang="ts">
import { Plus, X } from 'lucide-vue-next'
import type { FvgCandidateItem } from '@/types/fvg'
import { useFvgCandidateStore } from '@/stores/fvgCandidate'

const props = defineProps<{
  fvgCandidateItem: FvgCandidateItem
}>()

const fvgCandidateStore = useFvgCandidateStore()
</script>

<template>
  <span :class="[
      'cursor-default inline-flex items-center gap-1 px-1 py-0.5 text-xs',
      fvgCandidateItem.removed
        ? 'bg-gray-100 text-gray-500'
        : 'bg-violet-100 text-violet-700',
    ]">
    {{ fvgCandidateItem.algo_verb_token }}
    <span :class="fvgCandidateItem.removed ? 'text-gray-400' : 'text-violet-300'">·</span>
    {{ fvgCandidateItem.algo_noun_token }}
    <template v-if="fvgCandidateItem.algo_prep_token">
      <span :class="fvgCandidateItem.removed ? 'text-gray-400' : 'text-violet-300'">·</span>
      {{ fvgCandidateItem.algo_prep_token }}
    </template>
    <button v-if="!fvgCandidateItem.removed"
      class="cursor-pointer ml-0.5 text-red-500 hover:text-red-600 transition-colors"
      @click="fvgCandidateStore.toggleCandidateRemoved(props.fvgCandidateItem.id)">
      <X :size="10" />
    </button>
    <button v-else
      class="cursor-pointer ml-0.5 text-green-500 hover:text-green-600 transition-colors"
      @click="fvgCandidateStore.toggleCandidateRemoved(props.fvgCandidateItem.id)">
      <Plus :size="10" />
    </button>
  </span>
</template>
