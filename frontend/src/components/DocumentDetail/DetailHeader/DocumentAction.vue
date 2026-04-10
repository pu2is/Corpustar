<script setup lang="ts">
import {computed} from 'vue';
// types
import type { DocItem, ProcessingItem } from '@/types';
// stores
import { useProcessStore } from '@/stores/processStore';
// components
import FvgDisplayFilter from '@/components/DocumentDetail/FvgSentenceTable/FvgDisplayFilter.vue';
import FvgSearchModal from "@/components/DocumentDetail/Modals/FvgSearchModal.vue";
import Options from '@/components/DocumentDetail/FvgCandidatsOptions/Options.vue';

const props = defineProps<{
  document: DocItem;
  processes: ProcessingItem[];
}>();

const processStore = useProcessStore(); 

const hasFvgSearch = computed(() => props.processes.some(p => p.type === 'fvg'));

const segmentationId = computed(() => {
  const segmentationProcess = props.processes.find(p => p.type === 'sentence_segmentation');
  return segmentationProcess ? segmentationProcess.id : null;
});

const fvgSearchId = computed(() => {
  const fvgSearchProcess = props.processes.find(p => p.type === 'fvg');
  return fvgSearchProcess ? fvgSearchProcess.id : null;
});

// Actions
function startSentenceSegmentation(): void {
  processStore.segmentDocument(props.document.id);
}
</script>

<template>
  <div class="absolute right-0 top-1/2 -translate-y-1/2">
    <article v-if="!segmentationId">
      <button type="button"
        class="cursor-pointer bg-violet-300 text-violet-800 px-3 py-1.5 text-sm font-medium transition hover:opacity-80 
          disabled:cursor-not-allowed disabled:opacity-60"
        @click="startSentenceSegmentation()">
        Start segmentation
      </button>
    </article>
    <FvgSearchModal v-else-if="segmentationId && !hasFvgSearch" :segmentation-id="segmentationId" />
    <div v-else-if="segmentationId && hasFvgSearch" 
      class="flex items-center justify-center gap-1">
      <FvgDisplayFilter />
      <Options :fvg-id="fvgSearchId" :doc-filename="document.filename" />
    </div>
  </div>
</template>
