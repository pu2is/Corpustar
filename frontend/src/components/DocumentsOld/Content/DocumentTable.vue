<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { RefreshCcw } from 'lucide-vue-next'

import DocumentRow from '@/components/DocumentsOld/DocumentTable/DocumentRow.vue'
import { useDocumentStore } from '@/stores/documentStore'

const documentStore = useDocumentStore()
const { documents } = storeToRefs(documentStore)

const hasDocuments = computed(() => documents.value.length > 0)
const documentCount = computed(() => documents.value.length)

onMounted(() => {
  if (!documents.value.length) {
    void documentStore.getAllDocuments()
  }
})

function refreshDocuments(): void {
  void documentStore.getAllDocuments()
}

function removeDocument(id: string): void {
  void documentStore.removeDocument(id)
}
</script>

<template>
  <section class="min-h-0 flex flex-1 flex-col gap-3">
    <header class="shrink-0 flex items-end justify-between gap-3">
      <div class="flex items-start gap-2.5">
        <div class="flex-col cursor-default select-none">
          <h2 class="m-0 text-[0.95rem] font-semibold tracking-[0.01em] text-violet-950">
            Documents
          </h2>
          <p class="mt-0.5 text-xs text-text-muted">
            {{ documentCount }} item{{ documentCount === 1 ? '' : 's' }}
          </p>
        </div>

        <div class="cursor-pointer p-2 rounded-full bg-secondary/5 text-text-muted transition-colors hover:bg-secondary/20"
          aria-label="Refresh documents"
          @click="refreshDocuments">
          <RefreshCcw class="size-4" />
        </div>
      </div>
    </header>
    <div class="min-h-0 flex-1">
      <p v-if="!hasDocuments"
        class="m-0 px-2 py-1 text-sm text-text-muted">
        No documents found.
      </p>
      <template v-else>
        <div class="scroll-area h-full overflow-y-auto pr-1">
          <div class="flex flex-col gap-2">
            <DocumentRow v-for="document in documents"
              :key="document.id"
              :doc-item="document"
              @remove="removeDocument" />
          </div>
        </div>
      </template>
    </div>
  </section>
</template>
