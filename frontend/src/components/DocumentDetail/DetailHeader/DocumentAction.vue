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

// Actions
function startSentenceSegmentation(): void {
  processStore.segmentDocument(props.document.id);
}
</script>

<template>
  <div v-if="hasSegmentation" class="absolute right-0 top-1/2 -translate-y-1/2">
    <article>
      <button type="button"
        class="bg-yellow-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-60"
        @click="startSentenceSegmentation()">
      </button>
    </article>
  </div>

</template>
