<script setup lang="ts">
import { computed } from 'vue'
// stores
import { useDocumentStore } from '@/stores/documentStore';
import { useProcessStore } from '@/stores/processStore';
// components
import TopNav from '@/components/Nav/TopNav.vue';
// icons
// composables
import { getIdFromUrl } from '@/composables/useRouteId'
import DocumentInfo from '@/components/DocumentDetail/DetailHeader/DocumentInfo.vue';
import DocumentAction from '@/components/DocumentDetail/DetailHeader/DocumentAction.vue';

const docId = getIdFromUrl();
const documentStore = useDocumentStore();
const processStore = useProcessStore();

const document = computed(() => documentStore.getDocumentById(docId.value));
const processesOfDoc = computed(() => processStore.getProcessByDocId(docId.value));




</script>

<template>
  <main class="-mx-16 flex h-full flex-col overflow-hidden">
    <header class="relative flex min-h-16 items-center justify-between gap-4 bg-primary px-6 py-4 text-contrast shadow-sm">
      <TopNav />
    </header>

    <section class="ml-16 min-h-0 flex flex-col overflow-hidden px-16 py-6">
      <div v-if="document" class="relative pr-52">
        <DocumentInfo :document="document" />
        <DocumentAction :document=document :processes=processesOfDoc />

      
      </div>
    </section>
  </main>  
</template>
