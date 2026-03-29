<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronRight, RefreshCcw, Trash2 } from 'lucide-vue-next'

import { APP_ROUTES } from '@/config/routes'
import { useDocumentStore } from '@/stores/documentStore'
import type { DocItem } from '@/types/documents'
import { formatFileSize } from '@/utils/utils'

const documentStore = useDocumentStore()
const router = useRouter()
const documents = computed(() => documentStore.documents)
const documentCount = computed(() => documents.value.length)

function getDisplayName(docItem: DocItem): string {
  const displayName = docItem.display_name.trim()
  return displayName || docItem.filename
}

// actions
function refreshDocuments(): void {
  void documentStore.getAllDocuments()
}

function removeDocument(id: string): void {
  void documentStore.removeDocument(id)
}

function openDocumentDetail(id: string): void {
  void router.push(APP_ROUTES.documentDetail(id))
}
</script>

<template>
  <section class="flex flex-col gap-3">
    <header class="flex shrink-0 items-end justify-between gap-3">
      <div>
        <h2 class="text-[0.95rem] font-semibold tracking-[0.01em] text-violet-950">
          Documents
        </h2>
        <p class="mt-0.5 text-xs text-text-muted">
          {{ documentCount }} item{{ documentCount === 1 ? '' : 's' }}
        </p>
      </div>
      <button type="button"
        class="inline-flex cursor-pointer items-center justify-center rounded-full bg-secondary/5 p-2 text-text-muted transition-colors hover:bg-secondary/20"
        aria-label="Refresh documents"
        @click="refreshDocuments">
        <RefreshCcw class="size-4" />
      </button>
    </header>
    <div class="scroll-area min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
      <article v-for="document in documents"
        :key="document.id"
        class="flex cursor-pointer items-center justify-between gap-3 bg-background-elevated/60 p-4 text-[0.84rem] font-medium text-text-muted transition-colors hover:bg-background-elevated">
        <div class="min-w-0 flex-1">
          <p class="truncate">
            {{ getDisplayName(document) }}
          </p>
          <p class="mt-0.5 text-[0.72rem] font-normal text-text-muted/80">
            {{ formatFileSize(document.file_size) }}
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button type="button"
            class="inline-flex cursor-pointer items-center justify-center rounded p-1 text-text-muted/70 transition-colors hover:text-error"
            aria-label="Delete document"
            @click="removeDocument(document.id)">
            <Trash2 class="h-4 w-4 shrink-0" />
          </button>
          <button type="button"
            class="inline-flex cursor-pointer items-center justify-center rounded p-1 text-text-muted/70 transition-colors hover:text-violet-950"
            :aria-label="`Open ${getDisplayName(document)}`"
            @click="openDocumentDetail(document.id)">
            <ChevronRight class="h-4 w-4 shrink-0" />
          </button>
        </div>
      </article>
    </div>
  </section>
</template>
