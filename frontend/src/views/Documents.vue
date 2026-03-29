<script setup lang="ts">
import { computed } from 'vue';
// stores
import { useDocumentStore } from '@/stores/documentStore'
// components
import ImportDocument from '@/components/Documents/Widgets/ImportDocument.vue';
import TopNav from '@/components/Nav/TopNav.vue';
import DocumentTable from '@/components/Documents/DocumentTable.vue';

const documentStore = useDocumentStore();
const documents = computed(() => documentStore.documents);
const hasDocuments = computed(() => documents.value.length > 0);
</script>

<template>
  <main class="-mx-16 flex h-full flex-col overflow-hidden">
    <header class="relative flex min-h-16 items-center justify-between gap-4 bg-primary px-6 py-4 text-contrast shadow-sm">
      <TopNav />
      <ImportDocument />
    </header>
    <section v-if="!hasDocuments" class="flex flex-1 items-center justify-center p-6 px-16">
      <p class="text-sm text-muted">No documents yet. Import one to get started.</p>
    </section>
    <DocumentTable v-else class="min-h-0 flex-1 overflow-hidden p-6 px-16" />
  </main>
</template>
