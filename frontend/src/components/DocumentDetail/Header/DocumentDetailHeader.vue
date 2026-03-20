<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
// icons
import { BookOpenText } from 'lucide-vue-next'
// components
import WorkflowControl from '@/components/DocumentDetail/Header/WorkflowControl.vue'
// store
import { useDocumentStore } from '@/stores/documentStore'

const route = useRoute()
const docId = computed(() => {
  const param = route.params.doc_id
  return Array.isArray(param) ? (param[0] ?? '') : (param ?? '')
})

const documentStore = useDocumentStore();
const documents = computed(() => documentStore.documents);

const documentItem = computed(() => documents.value.find((doc) => doc.id === docId.value) ?? null);
const displayName = computed(() => documentItem.value?.displayName ?? '');
const formattedCharCount = computed(() => (documentItem.value?.textCharCount ?? 0).toLocaleString());
</script>

<template>
  <header class="rounded py-3 space-y-1">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h2 class="text-xl font-semibold text-violet-950">
        {{ displayName }}
      </h2>

      <WorkflowControl />
    </div>

    <div class="flex items gap-4">
      <span class="inline-flex items-center gap-2 py-1 text-sm bg-cyan-300 px-2 text-cyan-800">
        <BookOpenText class="h-3.5 w-3.5" />
        {{ formattedCharCount }} characters
      </span>

      <!-- <span class="inline-flex items-center gap-2 py-1 text-xs text-text-muted">
        id: {{ docId }}
      </span> -->
    </div>
  </header>
</template>
