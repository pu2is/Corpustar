<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
// stores
import { useDocumentStore } from '@/stores/documentStore';
import { useProcessStore } from '@/stores/processStore';
import { useSentenceStore } from '@/stores/sentenceStore';
// icons
// composables
import { getIdFromUrl } from '@/composables/useRouteId'
import { APP_ROUTES, isInRouteSection } from '@/config/routes'
// components
import TopNav from '@/components/Nav/TopNav.vue';
import DocumentInfo from '@/components/DocumentDetail/DetailHeader/DocumentInfo.vue';
import DocumentAction from '@/components/DocumentDetail/DetailHeader/DocumentAction.vue';
import SourceText from '@/components/DocumentDetail/SourceText.vue';  
import SentenceTable from '@/components/DocumentDetail/SentenceTable.vue';

const docId = getIdFromUrl();
const route = useRoute();
const documentStore = useDocumentStore();
const processStore = useProcessStore();
const sentenceStore = useSentenceStore();

const document = computed(() => documentStore.getDocumentById(docId.value));
const processesOfDoc = computed(() => processStore.getProcessByDocId(docId.value));
const hasSegmentation = computed(() => processesOfDoc.value.some(p => p.type === 'sentence_segmentation'));
const activeSegmentationId = computed(() => processStore.getSentenceSegmentationProcessByDocId(docId.value)?.id ?? '');

watch(
  [() => route.path, docId, activeSegmentationId],
  ([path, nextDocId, segmentationId]) => {
    if (!isInRouteSection(path, APP_ROUTES.documents) || !nextDocId || !segmentationId) {
      sentenceStore.$patch({ sentences: [] });
      return
    }

    void sentenceStore.getSentences(nextDocId, segmentationId).catch(() => {
      sentenceStore.$patch({ sentences: [] });
    });
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
        <DocumentInfo :document="document" />
        <DocumentAction :document=document :processes=processesOfDoc />
      </div>
      <SourceText v-if="!hasSegmentation && document" :documents="document" />
      <SentenceTable v-else-if="hasSegmentation && document" />
    </section>
  </main>  
</template>
