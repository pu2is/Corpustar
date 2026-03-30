<script setup lang="ts">
import {computed} from 'vue';
// types
import type { DocItem, ProcessingItem } from '@/types';
// stores
import { useProcessStore } from '@/stores/processStore';

const props = defineProps<{
  document: DocItem;
  processes: ProcessingItem[];
}>();

const processStore = useProcessStore(); 

const hasSegmentation = computed(() => props.processes.some(p => p.type === 'sentence_segmentation'));
// const hasLemmatize = computed(() => props.processes.some(p => p.type === 'lemma'));

// Actions
function startSentenceSegmentation(): void {
  processStore.segmentDocument(props.document.id);
}
</script>

<template>
  <div class="absolute right-0 top-1/2 -translate-y-1/2">
    <article v-if="!hasSegmentation">
      <button type="button"
        class="cursor-pointer bg-violet-300 text-violet-800 px-3 py-1.5 text-sm font-medium transition hover:opacity-80 
          disabled:cursor-not-allowed disabled:opacity-60"
        @click="startSentenceSegmentation()">
        Start segmentation
      </button>
    </article>
  </div>

</template>
