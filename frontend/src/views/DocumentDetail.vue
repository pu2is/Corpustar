<script setup lang="ts">
import { computed, watch } from 'vue'
// stores
import { useDocumentStore } from '@/stores/documentStore';
import { useProcessStore } from '@/stores/processStore';
import { useSentenceStore } from '@/stores/sentenceStore';
import { usePaginationStore } from '@/stores/local/paginationStore';
// icons
// composables
import { getIdFromUrl } from '@/composables/useRouteId'
// components
import TopNav from '@/components/Nav/TopNav.vue';
import DocumentInfo from '@/components/DocumentDetail/DetailHeader/DocumentInfo.vue';
import DocumentAction from '@/components/DocumentDetail/DetailHeader/DocumentAction.vue';
import SourceText from '@/components/DocumentDetail/SourceText.vue';  
import SentenceTable from '@/components/DocumentDetail/SentenceTable.vue';
import FvgSentenceTable from '@/components/DocumentDetail/FvgSentenceTable.vue';

const docId = getIdFromUrl();
const documentStore = useDocumentStore();
const processStore = useProcessStore();
const sentenceStore = useSentenceStore();
const paginationStore = usePaginationStore();

const document = computed(() => documentStore.getDocumentById(docId.value));
const processesOfDoc = computed(() => processStore.getProcessByDocId(docId.value));
const hasSegmentation = computed(() => processesOfDoc.value.some(p => p.type === 'sentence_segmentation'));
const hasFvgSearch = computed(() => processesOfDoc.value.some(p => p.type === 'fvg'));
const segmentationId = computed(() => processStore.getSentenceSegmentationProcessByDocId(docId.value)?.id ?? '');
// Backend function: `/api/sentences/length {segmentation_id: string}`
const sentenceLength = computed(() => -1);

watch(
  [docId, segmentationId],
  async ([nextDocId, nextSegmentationId]) => {
    if (!nextDocId || !nextSegmentationId) {
      return;
    }

    const savedCursor = paginationStore.paginationInfo.sentenceTable[nextSegmentationId]?.currentCursor ?? null;
    await sentenceStore.getSentences(nextDocId, nextSegmentationId, savedCursor);
  },
  { immediate: true },
);
</script>

<template>
  <main class="-mx-16 flex h-full flex-col overflow-hidden">
    <header class="relative flex min-h-16 items-center justify-between gap-4 bg-primary px-6 py-4 text-contrast shadow-sm">
      <TopNav />
    </header>

    <section class="ml-16 min-h-0 flex flex-1 flex-col overflow-hidden p-6 px-16">
      <div v-if="document" class="relative min-h-0 overflow-hidden">
        <DocumentInfo :document="document" :sentence-length="sentenceLength" />
        <DocumentAction :document=document :processes=processesOfDoc />
      </div>
      <SourceText v-if="!hasSegmentation && document" :documents="document" />
      <SentenceTable v-else-if="hasSegmentation && document && !hasFvgSearch" />
      <FvgSentenceTable v-else-if="hasSegmentation && document && hasFvgSearch" />
    </section>
  </main>  
</template>
